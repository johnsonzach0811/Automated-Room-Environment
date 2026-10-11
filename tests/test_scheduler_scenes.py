import copy
import datetime as dt
import json
import unittest
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

import scheduler
from devices import DeviceError, SimulatedLight
from validation import ConfigError, validate


def config():
    return {
        "devices": [
            {"name": "desk", "type": "simulated"},
            {"name": "shelf", "type": "simulated"},
        ],
        "presets": {
            "morning": {"power": True, "brightness": 30,
                        "color": {"r": 255, "g": 210, "b": 160}},
        },
        "scenes": {
            "movie": {
                "devices": {"desk": {"power": True, "brightness": 15,
                                     "color": {"r": 255, "g": 0, "b": 0}},
                            "shelf": {"power": False}},
                "transition": {"duration_sec": 0, "steps": 1},
            },
        },
        "schedules": [
            {"name": "Evening", "enabled": True, "time": "21:00",
             "days": ["Sat"], "scene": "movie"},
        ],
    }


def args_for(action, name):
    args = Mock()
    args.action = action
    args.name = name
    return args


def legacy_config():
    return {"device": {"ip": "127.0.0.1"}, "presets": {
        "morning": {"power": True, "brightness": 30,
                    "color": {"r": 255, "g": 210, "b": 160}}},
        "schedules": [{"name": "Morning", "enabled": True, "time": "06:45",
                       "days": ["Mon", "Tue", "Wed", "Thu"], "preset": "morning"}]}


class ValidationExtensionTests(unittest.TestCase):
    def test_full_config_valid(self):
        self.assertEqual(validate(config())["scenes"]["movie"]["devices"]["desk"]["brightness"], 15)

    def test_legacy_config_still_valid(self):
        validate(legacy_config())

    def test_devices_list_synthesizes_legacy_device(self):
        c = validate(config())
        self.assertEqual(c["device"]["ip"], "127.0.0.1")

    def test_bad_device_entries(self):
        for mutate in [
            lambda c: c.update(devices=[]),
            lambda c: c["devices"][0].update(type="toaster"),
            lambda c: c["devices"][0].update(ip="999.1.1.1"),
            lambda c: c["devices"].append({"name": "desk", "type": "simulated"}),
            lambda c: c["devices"][0].update(port=70000),
        ]:
            c = config(); mutate(c)
            with self.subTest(), self.assertRaises(ConfigError):
                validate(c)

    def test_neither_device_nor_devices(self):
        c = config(); del c["devices"]
        with self.assertRaises(ConfigError):
            validate(c)

    def test_scene_errors(self):
        for mutate in [
            lambda c: c["scenes"]["movie"]["devices"].update(ghost={"power": True}),
            lambda c: c["scenes"]["movie"]["devices"]["desk"].update(brightness=101),
            lambda c: c["scenes"].update(empty={"devices": {}}),
            lambda c: c["scenes"]["movie"].update(transition={"steps": 0}),
            lambda c: c["scenes"]["movie"]["devices"]["desk"].update(power="yes"),
        ]:
            c = config(); mutate(c)
            with self.subTest(), self.assertRaises(ConfigError):
                validate(c)

    def test_schedule_target_rules(self):
        c = config(); s = c["schedules"][0]
        s["preset"] = "morning"  # both preset and scene
        with self.assertRaises(ConfigError):
            validate(c)
        c = config(); del c["schedules"][0]["scene"]  # neither
        with self.assertRaises(ConfigError):
            validate(c)
        c = config(); c["schedules"][0]["scene"] = "missing"
        with self.assertRaises(ConfigError):
            validate(c)


class ApplySceneTests(unittest.TestCase):
    def test_apply_scene_drives_devices(self):
        c = config()
        with patch("scheduler.build_registry") as build:
            lights = {"desk": SimulatedLight("desk"), "shelf": SimulatedLight("shelf")}
            build.return_value = lights
            scheduler.apply_scene(c, "movie")
        self.assertEqual(lights["desk"].get_state().brightness, 15)
        self.assertFalse(lights["shelf"].get_state().power)

    def test_unknown_scene(self):
        with self.assertRaises(ConfigError):
            scheduler.apply_scene(config(), "nope")

    def test_scene_action_dispatch(self):
        with patch("scheduler.apply_scene") as apply:
            scheduler.run_action(args_for("scene", "movie"), config())
            apply.assert_called_once_with(config(), "movie")

    def test_scene_action_needs_name(self):
        with self.assertRaises(ConfigError):
            scheduler.run_action(args_for("scene", None), config())

    def test_scene_never_runs_on_validate(self):
        with patch("scheduler.apply_scene") as apply:
            scheduler.run_action(args_for("validate", None), config())
            apply.assert_not_called()


class SceneScheduleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name) / "last-runs.json"
        patcher = patch("scheduler.STATE", self.state); patcher.start(); self.addCleanup(patcher.stop)
        real_datetime = dt.datetime
        clock = patch("scheduler.dt.datetime"); now = clock.start(); self.addCleanup(clock.stop)
        now.now.return_value = real_datetime(2026, 10, 10, 21, 0)  # Saturday 21:00

    def test_scene_schedule_applies_once(self):
        with patch("scheduler.apply_scene") as apply:
            self.assertTrue(scheduler.check_schedules(config()))
            self.assertTrue(scheduler.check_schedules(config()))
            apply.assert_called_once_with(config(), "movie")
        self.assertEqual(json.loads(self.state.read_text())["Evening"], "2026-10-10 21:00")

    def test_scene_failure_not_recorded(self):
        with patch("scheduler.apply_scene", side_effect=DeviceError("down")):
            self.assertFalse(scheduler.check_schedules(config()))
        self.assertFalse(self.state.exists())


if __name__ == "__main__":
    unittest.main()
