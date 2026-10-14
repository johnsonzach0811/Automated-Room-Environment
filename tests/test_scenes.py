import unittest
from unittest.mock import patch

from devices import DeviceError, LightState, SimulatedLight
from scenes import Scene, SceneEngine, Transition, interpolate, scene_from_config


class InterpolateTests(unittest.TestCase):
    def test_single_step_returns_end(self):
        end = LightState(power=True, brightness=80, color=(10, 20, 30))
        self.assertEqual(interpolate(LightState(power=False), end, 1), [end])

    def test_linear_midpoint(self):
        start = LightState(power=True, brightness=0, color=(0, 0, 0))
        end = LightState(power=True, brightness=100, color=(100, 200, 50))
        frames = interpolate(start, end, 4)
        self.assertEqual(len(frames), 4)
        self.assertEqual(frames[1].brightness, 50)
        self.assertEqual(frames[1].color, (50, 100, 25))
        self.assertEqual(frames[-1], end)

    def test_power_off_holds_until_end(self):
        start = LightState(power=True, brightness=80, color=(255, 255, 255))
        end = LightState(power=False)
        frames = interpolate(start, end, 3)
        self.assertTrue(all(f.power for f in frames[:-1]))
        self.assertFalse(frames[-1].power)

    def test_invalid_steps(self):
        with self.assertRaises(DeviceError):
            interpolate(LightState(), LightState(), 0)


class SceneConfigTests(unittest.TestCase):
    def test_from_config(self):
        scene = scene_from_config("movie", {
            "devices": {"a": {"power": True, "brightness": 20,
                              "color": {"r": 1, "g": 2, "b": 3}}},
            "transition": {"duration_sec": 2.0, "steps": 4},
        })
        self.assertEqual(scene.name, "movie")
        self.assertEqual(scene.targets["a"],
                         LightState(power=True, brightness=20, color=(1, 2, 3)))
        self.assertEqual(scene.transition, Transition(duration_sec=2.0, steps=4))

    def test_defaults(self):
        scene = scene_from_config("x", {"devices": {"a": {"power": False}}})
        self.assertEqual(scene.targets["a"], LightState(power=False))
        self.assertEqual(scene.transition.steps, 1)

    def test_empty_targets_rejected(self):
        with self.assertRaises(DeviceError):
            Scene(name="empty", targets={})

    def test_bad_transition_rejected(self):
        with self.assertRaises(DeviceError):
            Transition(duration_sec=-1)
        with self.assertRaises(DeviceError):
            Transition(steps=0)


class SceneEngineTests(unittest.TestCase):
    def setUp(self):
        self.a = SimulatedLight("a")
        self.b = SimulatedLight("b")
        self.engine = SceneEngine({"a": self.a, "b": self.b})

    def test_apply_direct(self):
        scene = scene_from_config("night", {"devices": {
            "a": {"power": True, "brightness": 10, "color": {"r": 0, "g": 0, "b": 255}},
            "b": {"power": False}}})
        outcomes = self.engine.apply(scene)
        self.assertEqual(outcomes, {"a": "ok", "b": "ok"})
        self.assertEqual(self.a.get_state().brightness, 10)
        self.assertFalse(self.b.get_state().power)

    def test_unknown_device_fails_scene(self):
        scene = scene_from_config("bad", {"devices": {"ghost": {"power": True}}})
        with self.assertRaises(DeviceError) as ctx:
            self.engine.apply(scene)
        self.assertIn("ghost", str(ctx.exception))

    @patch("scenes.time.sleep")
    def test_transition_fades(self, sleep):
        self.a.apply_state(LightState(power=True, brightness=0, color=(0, 0, 0)))
        self.a.command_log.clear()
        scene = scene_from_config("fade", {
            "devices": {"a": {"power": True, "brightness": 100,
                              "color": {"r": 100, "g": 100, "b": 100}}},
            "transition": {"duration_sec": 4.0, "steps": 4},
        })
        self.engine.apply(scene)
        self.assertEqual(len(self.a.command_log), 4)
        self.assertEqual(self.a.command_log[-1].brightness, 100)
        self.assertEqual(sleep.call_count, 4)

    def test_device_failure_reports_device(self):
        self.a.fail_next()
        scene = scene_from_config("x", {"devices": {"a": {"power": True}}})
        with self.assertRaises(DeviceError) as ctx:
            self.engine.apply(scene)
        self.assertIn("a", str(ctx.exception))
        # Unaffected device still applied.
        self.assertEqual(self.b.command_log, [])

    def test_network_failure_recorded_per_device(self):
        import transport
        from devices import GoveeLight

        def boom(sock, ip, port, cmd, data):
            raise transport.ConnectionError("network down")

        net = GoveeLight("net", "192.168.4.99",
                         socket_factory=lambda: FakeSocketForScenes(),
                         sender=boom)
        engine = SceneEngine({"net": net, "b": self.b})
        scene = scene_from_config("x", {"devices": {"net": {"power": True},
                                                   "b": {"power": True}}})
        with self.assertRaises(DeviceError) as ctx:
            engine.apply(scene)
        self.assertIn("net", str(ctx.exception))
        # The healthy device still applied despite the network failure.
        self.assertTrue(self.b.get_state().power)


class FakeSocketForScenes:
    def __enter__(self):
        return object()

    def __exit__(self, *args):
        return False


if __name__ == "__main__":
    unittest.main()
