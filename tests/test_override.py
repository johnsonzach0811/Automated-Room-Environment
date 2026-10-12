import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import automation
import dashboard
import lan
import scheduler
from test_automation import config


class OverrideTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for module, attr, name in [(automation, 'STATUS', 'automation.json'),
                                   (automation, 'LOCK', 'control.lock'),
                                   (scheduler, 'STATE', 'runs.json')]:
            mock = patch.object(module, attr, self.root / name)
            mock.start(); self.addCleanup(mock.stop)

    def test_manual_change_pauses_and_resume_allows_due_schedule(self):
        with patch('scheduler.open_socket'), patch('scheduler.send'):
            dashboard.control(config(), {'brightness': 45})
        self.assertTrue(automation.read_status()['paused'])
        now = dt.datetime(2026, 10, 12, 6, 45)
        with patch('scheduler.dt.datetime') as clock, patch('scheduler.apply_preset') as apply:
            clock.now.return_value = now
            scheduler.check_schedules(config())
            apply.assert_not_called()
            automation.set_paused(False)
            scheduler.check_schedules(config())
            apply.assert_called_once()

    def test_failed_manual_send_still_pauses(self):
        with patch('scheduler.open_socket', side_effect=OSError('network down')):
            with self.assertRaises(OSError):
                dashboard.control(config(), {'power': False})
        self.assertTrue(automation.read_status()['paused'])

    def test_invalid_manual_control_does_not_pause(self):
        with self.assertRaises(ValueError):
            dashboard.control(config(), {'brightness': 999})
        self.assertFalse(automation.read_status()['paused'])

    def test_state_persists_across_process_restart(self):
        import subprocess, sys
        automation.set_paused(True)
        code = ('import automation; from pathlib import Path; '
                f'automation.STATUS=Path({str(automation.STATUS)!r}); '
                'assert automation.read_status()["paused"]')
        subprocess.run([sys.executable, '-B', '-c', code], check=True)

    def test_corrupt_state_stays_paused_until_explicit_resume(self):
        for raw in ['{', '[]', '{"paused":"false"}']:
            automation.STATUS.write_text(raw)
            self.assertTrue(automation.read_status()['paused'])
        automation.set_paused(False)
        self.assertFalse(automation.read_status()['paused'])

    def test_resume_does_not_replay_missed_minute(self):
        automation.set_paused(False)
        now = dt.datetime(2026, 10, 12, 6, 46)
        with patch('scheduler.dt.datetime') as clock, patch('scheduler.apply_preset') as apply:
            clock.now.return_value = now
            scheduler.check_schedules(config())
            apply.assert_not_called()

    def test_scheduler_and_manual_controls_share_process_lock(self):
        import subprocess, sys
        code = ('import automation; from pathlib import Path; '
                f'automation.LOCK=Path({str(automation.LOCK)!r}); '
                f'automation.STATUS=Path({str(automation.STATUS)!r}); '
                'automation.set_paused(True)')
        with automation.locked():
            child = subprocess.Popen([sys.executable, '-B', '-c', code])
            try:
                with self.assertRaises(subprocess.TimeoutExpired):
                    child.wait(timeout=0.15)
            finally:
                pass
        child.wait(timeout=3)
        self.assertEqual(child.returncode, 0)
        self.assertTrue(automation.read_status()['paused'])

    def test_paired_device_follows_identity_after_ip_change(self):
        device = {'ip': '192.0.2.1', 'identity': 'known'}
        with patch('lan.discover', return_value=[{'device': 'other', 'ip': '192.0.2.1'},
                                                {'device': 'known', 'ip': '192.0.2.2'}]):
            self.assertEqual(lan.resolve_device(device)['ip'], '192.0.2.2')
        with patch('lan.discover', return_value=[]):
            with self.assertRaises(OSError): lan.resolve_device(device)


if __name__ == '__main__':
    unittest.main()
