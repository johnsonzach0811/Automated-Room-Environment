"""Simulated devices for tests, demos, and development without hardware.

A SimulatedLight behaves like a real light from the caller's perspective —
it tracks state and records every applied state in command_log — but sends
nothing over the network. Optional failure injection lets tests exercise
error handling deterministically.
"""
from __future__ import annotations

import logging
import time

from .base import Device, DeviceError, LightState

log = logging.getLogger(__name__)


class SimulatedLight(Device):
    """In-memory light used when no physical hardware is available."""

    def __init__(self, name, latency_sec: float = 0.0):
        super().__init__(name)
        self.latency_sec = latency_sec
        self._state = LightState(power=False)
        self.command_log: list[LightState] = []
        self._failures_remaining = 0

    def fail_next(self, count: int = 1) -> None:
        """Make the next `count` apply_state calls raise DeviceError."""
        if count < 0:
            raise DeviceError("fail_next count must be >= 0")
        self._failures_remaining += count

    def apply_state(self, state: LightState) -> None:
        if self._failures_remaining > 0:
            self._failures_remaining -= 1
            raise DeviceError(f"Simulated light {self.name!r}: injected failure")
        if self.latency_sec > 0:
            time.sleep(self.latency_sec)
        log.debug("Simulated %s: applying %s", self.name, state)
        self._state = state
        self.command_log.append(state)

    def get_state(self) -> LightState:
        return self._state

    def reset(self) -> None:
        """Clear state and history (useful between tests)."""
        self._state = LightState(power=False)
        self.command_log.clear()
        self._failures_remaining = 0
