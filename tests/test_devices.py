import json
import unittest
from unittest.mock import Mock, patch

from devices import (
    DEVICE_TYPES, DeviceError, GoveeLight, LightState, SimulatedLight,
    build_device, build_registry,
)


class LightStateTests(unittest.TestCase):
    def test_defaults(self):
        state = LightState()
        self.assertEqual((state.brightness, state.color), (100, (255, 255, 255)))

    def test_invalid(self):
        for kwargs in [dict(brightness=101), dict(brightness=-1),
                       dict(color=(256, 0, 0)), dict(color=(0, 0)),
                       dict(brightness=True)]:
            with self.subTest(kwargs=kwargs), self.assertRaises(DeviceError):
                LightState(**kwargs)


class GoveeLightTests(unittest.TestCase):
    def test_apply_sends_govee_commands(self):
        sock = Mock()
        sent = []

        def fake_send(s, ip, port, cmd, data):
            sent.append((ip, port, cmd, data))

        light = GoveeLight("strip", "192.168.4.29", 4003,
                           socket_factory=lambda: FakeSocket(sock),
                           sender=fake_send)
        light.apply_state(LightState(power=True, brightness=30, color=(255, 210, 160)))
        self.assertEqual(
            [(cmd, data) for _, _, cmd, data in sent],
            [("turn", {"value": 1}),
             ("brightness", {"value": 30}),
             ("colorwc", {"color": {"r": 255, "g": 210, "b": 160},
                          "colorTemInKelvin": 0})],
        )
        self.assertEqual(light.get_state().brightness, 30)

    def test_off_sends_only_power(self):
        sent = []
        light = GoveeLight("strip", "192.168.4.29",
                           socket_factory=lambda: FakeSocket(Mock()),
                           sender=lambda s, ip, port, cmd, data: sent.append(cmd))
        light.apply_state(LightState(power=False))
        self.assertEqual(sent, ["turn"])

    def test_connection_error_propagates_unwrapped(self):
        import transport

        def boom(s, ip, port, cmd, data):
            raise transport.ConnectionError("down")

        light = GoveeLight("strip", "192.168.4.29",
                           socket_factory=lambda: FakeSocket(Mock()), sender=boom)
        with self.assertRaises(transport.ConnectionError):
            light.apply_state(LightState(power=True))


class FakeSocket:
    def __init__(self, sock):
        self.sock = sock

    def __enter__(self):
        return self.sock

    def __exit__(self, *args):
        return False


class SimulatedLightTests(unittest.TestCase):
    def test_state_and_log(self):
        light = SimulatedLight("fake")
        state = LightState(power=True, brightness=42, color=(1, 2, 3))
        light.apply_state(state)
        self.assertEqual(light.get_state(), state)
        self.assertEqual(light.command_log, [state])

    def test_failure_injection(self):
        light = SimulatedLight("fake")
        light.fail_next(2)
        with self.assertRaises(DeviceError):
            light.apply_state(LightState())
        with self.assertRaises(DeviceError):
            light.apply_state(LightState())
        light.apply_state(LightState())  # third call succeeds
        self.assertEqual(len(light.command_log), 1)

    def test_reset(self):
        light = SimulatedLight("fake")
        light.apply_state(LightState(power=True))
        light.fail_next()
        light.reset()
        self.assertEqual(light.command_log, [])
        self.assertFalse(light.get_state().power)
        # Failures are cleared too: next apply succeeds.
        light.apply_state(LightState(power=True))


class RegistryTests(unittest.TestCase):
    def test_legacy_device_becomes_default(self):
        registry = build_registry({"device": {"ip": "192.168.4.29"}})
        self.assertEqual(set(registry), {"default"})
        self.assertIsInstance(registry["default"], GoveeLight)

    def test_devices_list(self):
        registry = build_registry({"devices": [
            {"name": "a", "type": "govee", "ip": "192.168.4.29"},
            {"name": "b", "type": "simulated"},
        ]})
        self.assertIsInstance(registry["a"], GoveeLight)
        self.assertIsInstance(registry["b"], SimulatedLight)

    def test_unknown_type(self):
        with self.assertRaises(DeviceError):
            build_device({"name": "x", "type": "toaster", "ip": "192.168.4.2"})

    def test_duplicate_name(self):
        with self.assertRaises(DeviceError):
            build_registry({"devices": [
                {"name": "a", "type": "simulated"},
                {"name": "a", "type": "simulated"},
            ]})

    def test_empty_name_rejected(self):
        with self.assertRaises(DeviceError):
            SimulatedLight("  ")

    def test_device_types_advertised(self):
        self.assertEqual(set(DEVICE_TYPES), {"govee", "simulated"})


if __name__ == "__main__":
    unittest.main()
