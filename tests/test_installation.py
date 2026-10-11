import json
from pathlib import Path
import plistlib
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from scripts import install_launchd
from test_automation import config


class InstallationTests(unittest.TestCase):
    def test_install_preserves_config_retires_legacy_and_can_repeat(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp).resolve()
            repo = home / 'checkout'; repo.mkdir()
            (repo / 'scheduler.py').write_text('# test fixture')
            original = json.dumps(config())
            (repo / 'config.json').write_text(original)
            agents = home / 'Library/LaunchAgents'; agents.mkdir(parents=True)
            legacy = agents / 'com.roomautomation.morninglights.plist'
            legacy.write_bytes(plistlib.dumps({'Label':'com.roomautomation.morninglights'}))
            with patch('pathlib.Path.home', return_value=home), patch('sys.platform','darwin'), \
                 patch('sys.argv', ['install', '--repo', str(repo), '--apply']), \
                 patch('subprocess.run', return_value=Mock(returncode=0)) as commands:
                install_launchd.main()
                install_launchd.main()
            self.assertFalse(legacy.exists())
            self.assertEqual((repo / 'local/config.json').read_text(), original)
            backups = list((repo / 'local').glob('installation-backup-*'))
            self.assertEqual(len(backups), 2)
            self.assertTrue(any((backup / legacy.name).exists() for backup in backups))
            definition = plistlib.loads((agents / 'com.roomautomation.scheduler.plist').read_bytes())
            self.assertEqual(definition['ProgramArguments'][-2:], [str(repo / 'scheduler.py'),'check'])
            self.assertEqual({item['Minute'] for item in definition['StartCalendarInterval']},set(range(60)))
            bootstrap = [call for call in commands.call_args_list if call.args[0][1]=='bootstrap']
            self.assertEqual(len(bootstrap),2)
            self.assertTrue(all('com.roomautomation.scheduler.plist' in call.args[0][-1] for call in bootstrap))


if __name__ == '__main__':
    unittest.main()
