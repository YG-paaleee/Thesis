"""Artificial timing checks only; no measurements of deployed clocks."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from timing_report import probe_interval, report
from clock_reference import reference_interval, check
from capture_telemetry import Capture, NODE_HEADER


class TimingChecks(unittest.TestCase):
    def sample(self, **changes):
        value = dict(event='PROBE_REPLY', port='COM4', node=1, boot='boot1', probe='a' * 16,
                     local_ms=1000, send_epoch_ms=100000, receive_epoch_ms=100020,
                     send_mono_ms=5000, receive_mono_ms=5020)
        value.update(changes)
        return value

    def test_serial_probe_is_an_interval_not_exact_midpoint(self):
        result = probe_interval(self.sample())
        self.assertEqual((result['offset_lower_ms'], result['offset_upper_ms']), (98998, 99022))
        self.assertEqual(result['sample_uncertainty_ms'], 12)

    def test_backward_or_stepped_pc_clock_rejected(self):
        with self.assertRaises(ValueError):
            probe_interval(self.sample(receive_epoch_ms=99999))
        with self.assertRaises(ValueError):
            probe_interval(self.sample(receive_epoch_ms=100100))

    def test_missing_boot_rejected(self):
        with self.assertRaises(ValueError):
            probe_interval(self.sample(boot=None))

    def test_nonfinite_sample_rejected(self):
        with self.assertRaises(ValueError):
            probe_interval(self.sample(receive_epoch_ms=float('nan')))

    def test_asymmetric_lan_delays_still_bound_offset(self):
        # Actual reference-minus-client offset is 50 ms; forward 5 ms, return 15 ms.
        result = reference_interval(1000, 1055, 1056, 1021)
        self.assertEqual((result['reference_minus_laptop_lower_ms'], result['reference_minus_laptop_upper_ms']), (35, 55))
        self.assertLessEqual(result['reference_minus_laptop_lower_ms'], 50)
        self.assertGreaterEqual(result['reference_minus_laptop_upper_ms'], 50)

    def test_inconsistent_reference_timestamps_rejected(self):
        with self.assertRaises(ValueError):
            reference_interval(1000, 1100, 1110, 1005)

    def test_report_keeps_boots_separate_and_never_verifies(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'clock.jsonl'
            rows = [dict(event='CAPTURE', host='test', capture_id='fixture', session='S'),
                    self.sample(), self.sample(boot='boot2', probe='b' * 16)]
            path.write_text('\n'.join(json.dumps(r) for r in rows), encoding='utf-8')
            result = report(path)
            self.assertEqual(len(result['nodes']), 2)
            self.assertFalse(result['verified'])
            self.assertFalse(result['clean_close'])
            self.assertTrue(all(not r['verified'] for r in result['nodes']))

    def test_between_probe_clock_step_is_reported(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'clock.jsonl'
            rows = [dict(event='CAPTURE', host='test'), self.sample(),
                    self.sample(probe='b' * 16, local_ms=2000, send_epoch_ms=102000,
                        receive_epoch_ms=102020, send_mono_ms=6000, receive_mono_ms=6020)]
            path.write_text('\n'.join(json.dumps(r) for r in rows), encoding='utf-8')
            result = report(path)
            self.assertIn('laptop_wall_clock_changed_between_probes', result['nodes'][0]['warnings'])
            self.assertIsNone(result['nodes'][0]['sample_offset_intersection_ms'])

    def test_unanswered_probe_is_reported(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'clock.jsonl'
            rows = [dict(event='CAPTURE'), dict(event='PROBE_SEND', port='COM4', probe='missing'),
                    dict(event='CAPTURE_END')]
            path.write_text('\n'.join(json.dumps(r) for r in rows), encoding='utf-8')
            result = report(path)
            self.assertEqual(result['unanswered_probes'], 1)
            self.assertEqual(result['nodes'], [])

    def test_capture_probe_round_trip_to_sidecar(self):
        class Port:
            def write(self, payload): self.payload = payload
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            capture = Capture(Path(directory) / 'sample.csv', 0, 'S')
            port = Port()
            capture.probe_clock('COM4', port)
            probe = port.payload.decode().strip().split()[1]
            values = [''] * len(NODE_HEADER.split(','))
            values[0:8] = ['1000', '1', 'CLOCK', '0', '0', '0', '0', '']
            values[-1] = f'probe={probe};boot=boot1;seq=1'
            with contextlib.redirect_stdout(io.StringIO()):
                capture.handle_line('COM4', 'CSV,' + ','.join(values))
            capture.close()
            rows = [json.loads(line) for line in capture.clock_log.read_text().splitlines()]
            reply = [r for r in rows if r['event'] == 'PROBE_REPLY']
            self.assertEqual(len(reply), 1)
            self.assertEqual(reply[0]['boot'], 'boot1')
            self.assertEqual(reply[0]['probe'], probe)

    def test_reference_client_saves_reply_without_changing_clock(self):
        class FakeSocket:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def settimeout(self, _): pass
            def sendto(self, packet, address):
                self.request = json.loads(packet)
                self.address = address
            def recvfrom(self, _):
                response = dict(probe=self.request['probe'], reference_id='fake',
                                reference_receive_ms=1000055, reference_send_ms=1000056)
                return json.dumps(response).encode(), self.address
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            output = Path(directory) / 'comparison.json'
            with patch('clock_reference.socket.socket', return_value=FakeSocket()), \
                 patch('clock_reference.socket.gethostbyname', return_value='127.0.0.1'), \
                 patch('clock_reference.time.time_ns', side_effect=[1000000000000, 1000021000000]), \
                 patch('clock_reference.time.monotonic_ns', side_effect=[5000000000, 5021000000]), \
                 patch('clock_reference.time.sleep'), contextlib.redirect_stdout(io.StringIO()):
                check('fixture', 39393, 1, output)
            result = json.loads(output.read_text())
            self.assertFalse(result['clocks_adjusted'])
            self.assertFalse(result['verified'])
            self.assertNotIn('error', result['measurements'][0])


if __name__ == '__main__':
    unittest.main()
