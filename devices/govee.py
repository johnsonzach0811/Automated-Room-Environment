"""Govee LAN device control (H619D and compatible models).

Sends the same UDP commands the original lights.py/scheduler.py used:
"turn", "brightness", and "colorwc". Behavior is preserved exactly —
one socket per apply_state call, 0.3s spacing between commands, no
acknowledgement from the device.

The socket factory and sender are injectable so tests can run without
hardware or network access.
"""
from __future__ import annotations

import logging
import lan

from .base import Device, DeviceError, LightState
from transport import ConnectionError, open_socket, send as send_command

log = logging.getLogger(__name__)

DEFAULT_PORT = 4003


class GoveeLight(Device):
    """A Govee light strip controlled over the LAN API."""

    def __init__(self, name, ip, port=DEFAULT_PORT,
                 socket_factory=open_socket, sender=send_command, identity=None):
        super().__init__(name)
        self.identity = identity
        self.ip = ip
        self.port = port
        self._socket_factory = socket_factory
        self._sender = sender
        # LAN control is one-way; remember what we last asked for.
        self._state = LightState(power=False)

    def _send(self, sock, command, data):
        # transport.ConnectionError propagates unwrapped: it already names
        # the command and destination, and callers (scheduler, scenes) handle
        # it alongside DeviceError.
        self._sender(sock, self.ip, self.port, command, data)

    def apply_state(self, state: LightState) -> None:
        if self.identity:
            try:
                self.ip = lan.resolve_device(dict(ip=self.ip, port=self.port, identity=self.identity))["ip"]
            except OSError as exc:
                raise ConnectionError(str(exc)) from exc
        log.info("Govee %s: applying power=%s brightness=%s color=%s",
                 self.name, state.power, state.brightness, state.color)
        with self._socket_factory() as sock:
            self._send(sock, "turn", {"value": int(state.power)})
            if state.power:
                self._send(sock, "brightness", {"value": state.brightness})
                r, g, b = state.color
                self._send(sock, "colorwc", {
                    "color": {"r": r, "g": g, "b": b},
                    "colorTemInKelvin": 0,
                })
        self._state = state

    @property
    def supports_transitions(self):
        # Each scheduler run creates fresh adapters; desired state is not feedback.
        return False

    def get_state(self) -> LightState:
        return self._state
