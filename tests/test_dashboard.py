import copy
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import dashboard
from validation import ConfigError
from test_automation import config


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'config.json'
        self.path.write_text(json.dumps(config()))

    def test_save_preserves_device_presets_and_backup(self):
        before = self.path.read_bytes()
        original, revision, _ = dashboard.read_config(self.path)
        schedules = copy.deepcopy(original['schedules'])
        schedules[0]['time'] = '07:00'
        dashboard.save_schedules(self.path, dict(schedules=schedules, revision=revision))
        saved, _, _ = dashboard.read_config(self.path)
        self.assertEqual(saved['device'], original['device'])
        self.assertEqual(saved['presets'], original['presets'])
        self.assertEqual(saved['schedules'], schedules)
        self.assertEqual(self.path.with_suffix('.json.bak').read_bytes(), before)
        with self.assertRaises(ConfigError):
            dashboard.save_schedules(self.path, dict(schedules=schedules, revision=revision))

    def test_invalid_save_never_writes(self):
        before = self.path.read_bytes()
        _, revision, _ = dashboard.read_config(self.path)
        for schedules in [None, [{}], [dict(config()['schedules'][0], time='25:00')]]:
            with self.assertRaises(ConfigError):
                dashboard.save_schedules(self.path, dict(schedules=schedules, revision=revision))
            self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_controls_never_send(self):
        with patch('scheduler.open_socket') as sock:
            for data in [{}, {'power':1}, {'brightness':True}, {'brightness':101},
                         {'color':{'r':-1,'g':0,'b':0}}, {'preset':[]}, {'ip':'8.8.8.8'}]:
                with self.subTest(data=data), self.assertRaises(ConfigError):
                    dashboard.control(config(), data)
            sock.assert_not_called()

    def test_power_and_preset_reuse(self):
        with patch('scheduler.open_socket'), patch('scheduler.send') as send:
            dashboard.control(config(), {'power':False})
            send.assert_called_once()
            self.assertEqual(send.call_args.args[-2:], ('turn', {'value':0}))
        with patch('scheduler.apply_preset') as apply:
            dashboard.control(config(), {'preset':'morning'})
            apply.assert_called_once_with(config(), 'morning')

    def test_http_security_and_errors(self):
        server = dashboard.create_server(0, self.path)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        def request(path, data=None, headers=None, method=None):
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port)
            connection.request(method or ('GET' if data is None else 'POST'), path, data, headers or {})
            response = connection.getresponse()
            result = response.status, response.read()
            connection.close()
            return result
        self.assertEqual(request('/api/config')[0], 200)
        self.assertEqual(request('/', headers={'Host':'evil.example'})[0], 403)
        self.assertEqual(request('/api/control', '{}')[0], 403)
        self.assertEqual(request('/api/control', '{}', {'X-Room-Token':'é'})[0], 403)
        headers={'Content-Type':'application/json','X-Room-Token':server.token}
        self.assertEqual(request('/api/control','{}',dict(headers,Origin='https://evil.example'))[0],403)
        for body in ['{', '[]', '{"brightness":999}', '{"power":true,"unexpected":1}']:
            self.assertEqual(request('/api/control',body,headers)[0],400)
        with patch('scheduler.send') as send, patch('scheduler.open_socket'):
            status, body = request('/api/control','{"power":false}',headers)
            self.assertEqual(status,200)
            self.assertIn(b'not confirmed',body)
            send.assert_called_once()
        with patch('scheduler.open_socket', side_effect=OSError('down')):
            self.assertEqual(request('/api/control','{"power":true}',headers)[0],503)
        self.assertEqual(request('/missing')[0],404)
        self.assertEqual(request('/api/control','{}',dict(headers,**{'Content-Length':'65537'}))[0],400)


if __name__ == '__main__':
    unittest.main()
