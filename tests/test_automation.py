import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

import lights
import scheduler
import transport
from validation import ConfigError, validate


def config():
    return {"device": {"ip": "127.0.0.1"}, "presets": {
        "morning": {"power": True, "brightness": 30,
                    "color": {"r": 255, "g": 210, "b": 160}}},
        "schedules": [{"name": "Morning", "enabled": True, "time": "06:45",
                       "days": ["Mon", "Tue", "Wed", "Thu"], "preset": "morning"}]}


class ValidationTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate(config()), config())

    def test_invalid_values(self):
        cases = [("device", "ip", "invalid"), ("device", "port", True)]
        for section, key, value in cases:
            c = config(); c[section][key] = value
            with self.subTest(key=key), self.assertRaises(ConfigError):
                validate(c)
        for key, value in [("brightness", True), ("brightness", 101), ("power", 1), ("color", None)]:
            c = config(); c["presets"]["morning"][key] = value
            with self.subTest(key=key), self.assertRaises(ConfigError):
                validate(c)
        for key, value in [("preset", []), ("preset", "missing"), ("time", "6:45"),
                           ("days", ["Mon", "Mon"]), ("enabled", "true")]:
            c = config(); c["schedules"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ConfigError):
                validate(c)

    def test_duplicate_schedule(self):
        c = config(); c["schedules"].append(copy.deepcopy(c["schedules"][0]))
        with self.assertRaises(ConfigError): validate(c)

    def test_validate_action_never_sends(self):
        with patch('scheduler.apply_preset') as apply:
            scheduler.run_action(Mock(action='validate'), config())
            apply.assert_not_called()


class TransportTests(unittest.TestCase):
    @patch('transport.time.sleep')
    def test_packet_and_success(self, sleep):
        sock = Mock(); sock.sendto.side_effect = lambda data, address: len(data)
        transport.send(sock, '127.0.0.1', 4003, 'turn', {'value': 1})
        packet, address = sock.sendto.call_args.args
        self.assertEqual(json.loads(packet), {'msg': {'cmd': 'turn', 'data': {'value': 1}}})
        self.assertEqual(address, ('127.0.0.1', 4003))
        sleep.assert_called_once_with(0.3)

    @patch('transport.time.sleep')
    def test_recovery(self, sleep):
        sock = Mock()
        sock.sendto.side_effect = lambda data, address: self.recover(data)
        self.calls = 0
        transport.send(sock, '127.0.0.1', 4003, 'turn', {'value': 1})
        self.assertEqual(sock.sendto.call_count, 2)

    def recover(self, data):
        self.calls += 1
        if self.calls == 1: raise OSError('network down')
        return len(data)

    @patch('transport.time.sleep')
    def test_exhaustion_and_backoff(self, sleep):
        for failure in [OSError('network down'), TimeoutError('timed out')]:
            sock = Mock(); sock.sendto.side_effect = failure
            with self.assertRaises(transport.ConnectionError):
                transport.send(sock, '127.0.0.1', 4003, 'turn', {'value': 1})
            self.assertEqual(sock.sendto.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2, 1, 2])

    @patch('transport.time.sleep')
    def test_short_send(self, sleep):
        sock = Mock(); sock.sendto.return_value = 0
        with self.assertRaises(transport.ConnectionError):
            transport.send(sock, '127.0.0.1', 4003, 'turn', {'value': 1})

    def test_socket_failure(self):
        with patch('transport.socket.socket', side_effect=OSError('unavailable')):
            with self.assertRaises(transport.ConnectionError): transport.open_socket()

    def test_timeout_and_cleanup(self):
        sock = Mock()
        with patch('transport.socket.socket', return_value=sock):
            self.assertIs(transport.open_socket(), sock)
            sock.settimeout.assert_called_once_with(2.0)
            sock.settimeout.side_effect = OSError('failed')
            with self.assertRaises(transport.ConnectionError): transport.open_socket()
            sock.close.assert_called_once()


class PresetTests(unittest.TestCase):
    def test_partial_failure_closes_socket(self):
        sock = MagicMock()
        with patch('scheduler.open_socket', return_value=sock), patch('scheduler.send', side_effect=transport.ConnectionError('down')) as send:
            with self.assertRaises(transport.ConnectionError): scheduler.apply_preset(config(), 'morning')
            self.assertEqual(send.call_count, 1)
            sock.__exit__.assert_called_once()

    def test_off_sends_only_power(self):
        c = config(); c['presets']['morning']['power'] = False
        with patch('scheduler.open_socket'), patch('scheduler.send') as send:
            scheduler.apply_preset(c, 'morning')
            self.assertEqual(send.call_count, 1)
            self.assertEqual(send.call_args.args[-1], {'value': 0})

    def test_legacy_uses_transport(self):
        with patch('lights.send_command') as send:
            sock = Mock(); lights.send(sock, 'turn', {'value': 1})
            send.assert_called_once_with(sock, lights.LIGHT_IP, lights.PORT, 'turn', {'value': 1})


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name) / 'last-runs.json'
        self.state_patch = patch('scheduler.STATE', self.state); self.state_patch.start(); self.addCleanup(self.state_patch.stop)
        self.datetime = dt.datetime
        self.clock = patch('scheduler.dt.datetime'); self.now = self.clock.start(); self.addCleanup(self.clock.stop)
        self.now.now.return_value = self.datetime(2026, 10, 12, 6, 45)

    def test_success_and_duplicate(self):
        with patch('scheduler.apply_preset') as apply:
            self.assertTrue(scheduler.check_schedules(config()))
            self.assertTrue(scheduler.check_schedules(config()))
            apply.assert_called_once()
        self.assertEqual(json.loads(self.state.read_text())['Morning'], '2026-10-12 06:45')

    def test_failure_not_recorded_and_other_schedule_runs(self):
        c = config(); second = copy.deepcopy(c['schedules'][0]); second['name'] = 'Other'; c['schedules'].append(second)
        with patch('scheduler.apply_preset', side_effect=[transport.ConnectionError('down'), None]):
            self.assertFalse(scheduler.check_schedules(c))
        self.assertEqual(json.loads(self.state.read_text()), {'Other': '2026-10-12 06:45'})
        with patch('scheduler.apply_preset') as apply:
            self.assertTrue(scheduler.check_schedules(c)); apply.assert_called_once()

    def test_outside_schedule(self):
        for now in [self.datetime(2026, 10, 16, 6, 45), self.datetime(2026, 10, 12, 6, 44)]:
            self.now.now.return_value = now
            with patch('scheduler.apply_preset') as apply:
                scheduler.check_schedules(config()); apply.assert_not_called()

    def test_disabled(self):
        c = config(); c['schedules'][0]['enabled'] = False
        with patch('scheduler.apply_preset') as apply:
            scheduler.check_schedules(c); apply.assert_not_called()


if __name__ == '__main__': unittest.main()
