"""Device registry: build Device objects from configuration entries.

Supported types:
  govee      — Govee light over LAN (requires ip; port defaults to 4003)
  simulated  — in-memory device for tests and development (no network)

A config entry looks like:
  {"name": "desk-strip", "type": "govee", "ip": "192.168.4.29", "port": 4003}
"""
from __future__ import annotations

from .base import Device, DeviceError, LightState
from .govee import GoveeLight, DEFAULT_PORT
from .simulated import SimulatedLight

DEVICE_TYPES = {
    "govee": GoveeLight,
    "simulated": SimulatedLight,
}


def build_device(entry: dict) -> Device:
    """Build a Device from a validated config entry."""
    name = entry.get("name")
    dtype = entry.get("type", "govee")
    if dtype not in DEVICE_TYPES:
        raise DeviceError(
            f"Unknown device type {dtype!r} for device {name!r}; "
            f"supported types: {', '.join(sorted(DEVICE_TYPES))}"
        )
    if dtype == "govee":
        return GoveeLight(name, entry["ip"], entry.get("port", DEFAULT_PORT))
    return SimulatedLight(name)


def build_registry(config: dict) -> dict[str, Device]:
    """Build every configured device, keyed by name.

    Accepts the legacy single-device config ({"device": {...}}) and the new
    {"devices": [...]} list. The legacy device is registered under the name
    "default" unless a devices list already defines it.
    """
    registry: dict[str, Device] = {}
    for entry in config.get("devices", []):
        device = build_device(entry)
        if device.name in registry:
            raise DeviceError(f"Duplicate device name: {device.name!r}")
        registry[device.name] = device
    if "device" in config and "default" not in registry:
        legacy = dict(config["device"])
        legacy.setdefault("name", "default")
        legacy.setdefault("type", "govee")
        registry["default"] = build_device(legacy)
    return registry


__all__ = [
    "DEVICE_TYPES",
    "Device",
    "DeviceError",
    "GoveeLight",
    "LightState",
    "SimulatedLight",
    "build_device",
    "build_registry",
]
