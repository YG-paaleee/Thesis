"""Logging preparation checks; no actual COM port is opened."""
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from capture_telemetry import Capture, NODE_HEADER

KIT = Path(__file__).resolve().parents[4] / 'Documents' / 'GROUP LOGGING KIT'
spec = importlib.util.spec_from_file_location('kit_record', KIT / 'record.py')
kit_record = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit_record)


def event_line(node, event='CONFIG', detail='cfg=baseline;boot=test;seq=1'):
    values = [''] * len(NODE_HEADER.split(','))
    values[:8] = ['1000', str(node), event, '0', '0', '0', '0', '']
    values[-1] = detail
    return 'CSV,' + ','.join(values)


class LoggingSetup(unittest.TestCase):
    def test_wrong_board_stops_recording(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            capture = Capture(Path(directory) / 'test.csv', 0, 'S', expected_node=2)
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                capture.handle_line('COM4', event_line(1))
            self.assertTrue(capture.stop.is_set())
            self.assertIn('Wrong board', capture.error_reason)
            capture.close()

    def test_wrong_configuration_stops_recording(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            capture = Capture(Path(directory) / 'test.csv', 0, 'S', expected_config='baseline')
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                capture.handle_line('COM4', event_line(1, detail='cfg=dev;boot=test;seq=1'))
            self.assertTrue(capture.stop.is_set())
            self.assertIn('Wrong firmware', capture.error_reason)
            capture.close()

    def test_expected_boot_is_accepted(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            capture = Capture(Path(directory) / 'test.csv', 0, 'S', expected_node=1, expected_config='baseline')
            with contextlib.redirect_stdout(io.StringIO()):
                capture.handle_line('COM4', event_line(1))
            self.assertFalse(capture.stop.is_set())
            self.assertIsNone(capture.error_reason)
            capture.close()

    def test_existing_record_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'test.csv'
            path.write_text('keep this original', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                Capture(path, 0, 'S')
            self.assertEqual(path.read_text(), 'keep this original')

    def test_existing_raw_log_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            raw = root / 'test_raw.log'
            raw.write_text('original raw', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                Capture(root / 'test.csv', 0, 'S')
            self.assertFalse((root / 'test.csv').exists())

    def test_guided_command_records_without_traffic_injection(self):
        output, command = kit_record.recording_command(Path('folder with spaces'), Path(sys.executable),
            2, 'COM4', 'baseline-pilot-01', 'laptop2', 'teststamp')
        self.assertIn('V2-laptop2-teststamp', output.name)
        self.assertNotIn('--inject', command)
        self.assertIn('--expected-node', command)
        self.assertIn('--expected-config', command)
        self.assertIn('--no-time-sync', command)
        self.assertIn('--clock-probe-every', command)

    def test_bad_labels_and_ports_are_rejected(self):
        for label in ('../escape', 'hello world', '', 'a/b'):
            with self.assertRaises(ValueError):
                kit_record.safe_label(label)
        with self.assertRaises(ValueError):
            kit_record.recording_command(Path('.'), Path(sys.executable), 9, 'COM4', 'S', 'L', 'T')
        with self.assertRaises(ValueError):
            kit_record.recording_command(Path('.'), Path(sys.executable), 1, 'COM4;bad', 'S', 'L', 'T')

    def test_dry_run_does_not_open_hardware_or_create_logs(self):
        result = subprocess.run([sys.executable, '-B', str(KIT / 'record.py'), '--dry-run',
            '--node', '2', '--port', 'COM4', '--session', 'baseline-pilot-01', '--laptop', 'laptop2',
            '--power', 'laptop USB'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"hardware_verified": false', result.stdout)


if __name__ == '__main__':
    unittest.main()
