import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import automation
import dashboard
import scheduler
from devices import GoveeLight, default_device_name
from scenes import Scene, SceneEngine, Transition
from devices import LightState, SimulatedLight
from validation import ConfigError, validate
from test_scheduler_scenes import config


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for module, key, filename in [(automation, 'STATUS', 'override.json'),
                                      (automation, 'LOCK', 'lock'),
                                      (scheduler, 'STATE', 'runs.json')]:
            patcher = patch.object(module, key, self.root / filename)
            patcher.start(); self.addCleanup(patcher.stop)

    def test_validation_does_not_mutate_or_create_network_device(self):
        c = config(); original = copy.deepcopy(c)
        validate(c)
        self.assertEqual(c, original)
        registry = scheduler.registry_for(c)
        self.assertEqual(set(registry), {'desk', 'shelf'})
        self.assertIsInstance(registry[default_device_name(c)], SimulatedLight)
        c['default_device'] = 'shelf'; validate(c)
        self.assertEqual(default_device_name(c), 'shelf')

    def test_conflicting_default_and_invalid_identity(self):
        for entry in [dict(name='default', type='simulated'), dict(name='bad', type='govee', ip='127.0.0.1', identity=[])]:
            c = config(); c['device'] = {'ip': '127.0.0.1'}; c['devices'].append(entry)
            with self.assertRaises(ConfigError): validate(c)

    def test_bad_transition_bounds(self):
        for values in [{'duration_sec': float('nan')}, {'duration_sec': float('inf')},
                       {'duration_sec': 31}, {'steps': 61}, {'duration_sec': True}]:
            c = config(); c['scenes']['movie']['transition'] = values
            with self.assertRaises(ConfigError): validate(c)
            with self.assertRaises(Exception): Transition(**values)

    def test_save_preserves_scene_targets_and_config(self):
        path = self.root / 'config.json'; path.write_text(json.dumps(config()))
        before, revision, _ = dashboard.read_config(path)
        schedules = copy.deepcopy(before['schedules']); schedules[0]['time'] = '22:00'
        dashboard.save_schedules(path, {'schedules': schedules, 'revision': revision})
        saved, _, _ = dashboard.read_config(path)
        self.assertEqual(saved['schedules'][0]['scene'], 'movie')
        self.assertEqual(saved['devices'], before['devices'])
        self.assertEqual(saved['scenes'], before['scenes'])
        self.assertNotIn('device', saved)

    def test_manual_scene_pauses_even_on_failure(self):
        with patch('scheduler.apply_scene', side_effect=OSError('offline')):
            with self.assertRaises(OSError): dashboard.control(config(), {'scene': 'movie'})
        self.assertTrue(automation.read_status()['paused'])

    def test_unreachable_other_device_does_not_block_scene(self):
        c = config(); c['devices'].append(dict(name='offline', type='govee', ip='127.0.0.1', identity='missing'))
        with patch('lan.discover', side_effect=AssertionError('unrelated device queried')):
            scheduler.apply_scene(c, 'movie')

    def test_govee_fade_applies_once_without_assumed_state(self):
        light = GoveeLight('light', '127.0.0.1')
        with patch.object(light, 'apply_state') as apply, patch.object(light, 'get_state', side_effect=AssertionError):
            SceneEngine({'light': light}).apply(Scene('fade', {'light': LightState()}, Transition(5, 5)))
            apply.assert_called_once()

    def test_transition_accounts_for_send_time(self):
        light = SimulatedLight('light')
        with patch('scenes.time.monotonic', side_effect=[0, .4, 1.4]), patch('scenes.time.sleep') as sleep:
            SceneEngine({'light': light}).apply(Scene('fade', {'light': LightState()}, Transition(2, 2)))
        self.assertEqual([round(c.args[0], 2) for c in sleep.call_args_list], [.6, .6])

    def test_corrupt_history_never_replays(self):
        for data in ['{', '[]', '{"Evening": 123}']:
            scheduler.STATE.write_text(data)
            with patch('scheduler.apply_scene') as apply:
                self.assertFalse(scheduler.check_schedules(config())); apply.assert_not_called()

    def test_restart_and_paused_minute_do_not_replay(self):
        c = config(); now = dt.datetime(2026, 10, 10, 21, 0)
        with patch('scheduler.dt.datetime') as clock, patch('scheduler.apply_scene') as apply:
            clock.now.return_value = now
            scheduler.check_schedules(c)
            scheduler.check_schedules(json.loads(json.dumps(c)))
            apply.assert_called_once()
            automation.set_paused(True)
            clock.now.return_value = now + dt.timedelta(days=7)
            scheduler.check_schedules(c)
            automation.set_paused(False)
            clock.now.return_value += dt.timedelta(minutes=1)
            scheduler.check_schedules(c)
            apply.assert_called_once()

    def test_atomic_history_failure_preserves_previous_file(self):
        scheduler.STATE.write_text('{"previous": "minute"}')
        with patch('os.replace', side_effect=OSError('disk full')):
            with self.assertRaises(OSError): scheduler.write_runs({'new': 'minute'})
        self.assertEqual(json.loads(scheduler.STATE.read_text()), {'previous': 'minute'})
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['runs.json'])
