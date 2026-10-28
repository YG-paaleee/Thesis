"""LAN timing comparison without adjusting any laptop clocks.

Keep one reference server running before and after deployment. Other laptops
check it while connected to the same LAN. The service is measurement-only;
its reference is monotonic time anchored at server start, not certified UTC.
"""
import argparse
import json
import math
import socket
import time
import uuid
from pathlib import Path


def reference_interval(local_send_ms, ref_receive_ms, ref_send_ms, local_receive_ms):
    values = [local_send_ms, ref_receive_ms, ref_send_ms, local_receive_ms]
    if not all(isinstance(v, (float, int)) and math.isfinite(v) for v in values):
        raise ValueError('Nonfinite clock values')
    if local_receive_ms < local_send_ms or ref_send_ms < ref_receive_ms:
        raise ValueError('Clock moved backwards')
    # Causal network bounds, without assuming symmetric network delay.
    lower = ref_send_ms - local_receive_ms
    upper = ref_receive_ms - local_send_ms
    if lower > upper:
        raise ValueError('Inconsistent timestamps or clock step')
    return dict(reference_minus_laptop_lower_ms=lower,
                reference_minus_laptop_upper_ms=upper,
                midpoint_ms=(lower + upper) / 2, sample_uncertainty_ms=(upper - lower) / 2)


def serve(bind, port):
    identity = uuid.uuid4().hex
    anchor_epoch, anchor_mono = time.time_ns(), time.monotonic_ns()
    def now():
        return (anchor_epoch + time.monotonic_ns() - anchor_mono) / 1_000_000
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((bind, port))
        print(f'Reference {identity}, listening on {bind}:{port}. Keep this running through the session.', flush=True)
        while True:
            packet, address = sock.recvfrom(2048)
            received = now()
            try:
                request = json.loads(packet)
                token = request['probe']
                if not isinstance(token, str) or len(token) != 32:
                    continue
            except (ValueError, KeyError, TypeError):
                continue
            response = dict(probe=token, reference_id=identity,
                            reference_receive_ms=received, reference_send_ms=now())
            sock.sendto(json.dumps(response).encode('utf-8'), address)


def check(host, port, count, output):
    results = []
    address = socket.gethostbyname(host)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(2)
        for _ in range(count):
            probe = uuid.uuid4().hex
            mono_start, epoch_start = time.monotonic_ns() / 1_000_000, time.time_ns() / 1_000_000
            sock.sendto(json.dumps(dict(probe=probe)).encode(), (address, port))
            try:
                while True:
                    packet, remote = sock.recvfrom(2048)
                    mono_end, epoch_end = time.monotonic_ns() / 1_000_000, time.time_ns() / 1_000_000
                    response = json.loads(packet)
                    if remote[0] != address or remote[1] != port or response.get('probe') != probe:
                        raise ValueError('Unexpected reply; no clock sample accepted')
                    if abs((epoch_end - epoch_start) - (mono_end - mono_start)) > 5:
                        raise ValueError('Laptop clock changed during sample')
                    interval = reference_interval(epoch_start, response['reference_receive_ms'],
                                                  response['reference_send_ms'], epoch_end)
                    results.append(dict(local_send_ms=epoch_start,
                        local_receive_ms=epoch_end, **response, **interval))
                    break
            except (socket.timeout, ValueError, KeyError, TypeError) as error:
                results.append(dict(probe=probe, error=str(error)))
            time.sleep(0.2)
    result = dict(host=socket.gethostname(), reference_host=host,
                  clocks_adjusted=False, verified=False, measurements=results)
    # This is a saved comparison, not a change to the operating system clock.
    with Path(output).open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(f'Saved {sum("error" not in r for r in results)} valid samples to {output}. No laptop clock was adjusted.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    server = modes.add_parser('serve')
    server.add_argument('--bind', default='0.0.0.0')
    server.add_argument('--port', type=int, default=39393)
    client = modes.add_parser('check')
    client.add_argument('host')
    client.add_argument('--port', type=int, default=39393)
    client.add_argument('--count', type=int, default=10)
    client.add_argument('--out', required=True)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('Port must be between 1 and 65535')
    if args.mode == 'check' and not 1 <= args.count <= 100:
        parser.error('Count must be between 1 and 100')
    if args.mode == 'serve':
        try:
            serve(args.bind, args.port)
        except KeyboardInterrupt:
            pass
    else:
        check(args.host, args.port, args.count, args.out)


if __name__ == '__main__':
    main()
