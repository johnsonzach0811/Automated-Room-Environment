"""Device abstraction for the Automated Room Environment.

A Device is anything the room can control: today Govee lights over LAN,
tomorrow TVs, speakers, and other connected hardware. New device types are
added by subclassing Device and registering the type in devices/__init__.py.

Govee control sends use one-way UDP: "success" means the operating system
accepted a datagram, never that the device acknowledged it. These adapters track requested state locally; explicit status queries live
in lan.py. Requested state is not used to start Govee fades.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass


class DeviceError(Exception):
    """A device could not apply a requested state."""


@dataclass(frozen=True)
class LightState:
    """Desired state for a light-class device."""
    power: bool = True
    brightness: int = 100  # 0-100
    color: tuple[int, int, int] = (255, 255, 255)  # RGB, each 0-255

    def __post_init__(self):
        if type(self.power) is not bool:
            raise DeviceError("power must be true or false")
        if type(self.brightness) is not int or not 0 <= self.brightness <= 100:
            raise DeviceError(f"brightness must be an integer 0-100, got {self.brightness!r}")
        if (len(self.color) != 3 or
                any(type(c) is not int or not 0 <= c <= 255 for c in self.color)):
            raise DeviceError(f"color must be three integers 0-255, got {self.color!r}")


class Device(abc.ABC):
    """Base class for every controllable room device."""

    def __init__(self, name: str):
        if not name or not name.strip():
            raise DeviceError("device name must be a nonempty string")
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @abc.abstractmethod
    def apply_state(self, state: LightState) -> None:
        """Apply a state. Raises DeviceError when the device cannot comply."""

    @abc.abstractmethod
    def get_state(self) -> LightState:
        """Last-applied state (devices may not support reading hardware)."""

    @property
    def supports_transitions(self) -> bool:
        """Whether the device can fade between states over time."""
        return True
