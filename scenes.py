"""Reusable scene engine: named scenes applied to any set of devices.

A scene maps device names to desired states plus an optional transition:

    "movie-night": {
        "devices": {
            "desk-strip": {"power": True, "brightness": 20,
                           "color": {"r": 255, "g": 120, "b": 40}},
            "shelf-strip": {"power": False}
        },
        "transition": {"duration_sec": 5.0, "steps": 10}
    }

Transitions linearly interpolate brightness and color from each device's
current state to the target over `steps` steps. Devices whose
supports_transitions is False, or scenes without a transition, apply the
target state directly.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from devices import Device, DeviceError, LightState
from transport import ConnectionError

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Transition:
    duration_sec: float = 0.0
    steps: int = 1

    def __post_init__(self):
        if self.duration_sec < 0:
            raise DeviceError("transition duration_sec must be >= 0")
        if type(self.steps) is not int or self.steps < 1:
            raise DeviceError("transition steps must be an integer >= 1")


@dataclass(frozen=True)
class Scene:
    name: str
    targets: dict[str, LightState]
    transition: Transition = field(default_factory=Transition)

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise DeviceError("scene name must be a nonempty string")
        if not self.targets:
            raise DeviceError(f"scene {self.name!r} must target at least one device")


def interpolate(start: LightState, end: LightState, steps: int) -> list[LightState]:
    """Linear interpolation from start to end, inclusive of both endpoints."""
    if steps < 1:
        raise DeviceError("interpolate steps must be >= 1")
    if steps == 1:
        return [end]
    frames = []
    for i in range(1, steps + 1):
        t = i / steps
        brightness = round(start.brightness + (end.brightness - start.brightness) * t)
        color = tuple(
            round(s + (e - s) * t) for s, e in zip(start.color, end.color)
        )
        # Power flips at the end of the fade so lights dim out before switching off.
        power = end.power if (t == 1.0 or end.power) else start.power
        frames.append(LightState(power=power, brightness=brightness, color=color))
    return frames


def scene_from_config(name: str, raw: dict) -> Scene:
    """Build a Scene from a validated config entry."""
    targets = {}
    for device_name, settings in raw["devices"].items():
        color = settings.get("color", {"r": 255, "g": 255, "b": 255})
        targets[device_name] = LightState(
            power=settings.get("power", True),
            brightness=settings.get("brightness", 100),
            color=(color["r"], color["g"], color["b"]),
        )
    transition = Transition()
    if "transition" in raw:
        transition = Transition(
            duration_sec=raw["transition"].get("duration_sec", 0.0),
            steps=raw["transition"].get("steps", 1),
        )
    return Scene(name=name, targets=targets, transition=transition)


class SceneEngine:
    """Applies scenes to a registry of devices."""

    def __init__(self, devices: dict[str, Device]):
        self.devices = dict(devices)

    def apply(self, scene: Scene) -> dict[str, str]:
        """Apply a scene; returns per-device outcome ('ok' or error message)."""
        outcomes: dict[str, str] = {}
        for device_name, target in scene.targets.items():
            device = self.devices.get(device_name)
            if device is None:
                outcomes[device_name] = f"unknown device {device_name!r}"
                log.error("Scene %s: %s", scene.name, outcomes[device_name])
                continue
            try:
                self._apply_to_device(device, target, scene.transition)
                outcomes[device_name] = "ok"
            except (DeviceError, ConnectionError) as exc:
                outcomes[device_name] = str(exc)
                log.error("Scene %s: device %s failed: %s", scene.name, device_name, exc)
        failed = {k: v for k, v in outcomes.items() if v != "ok"}
        if failed:
            raise DeviceError(f"Scene {scene.name!r} failed for: {failed}")
        log.info("Scene %s applied to %d device(s)", scene.name, len(outcomes))
        return outcomes

    def _apply_to_device(self, device: Device, target: LightState, transition: Transition) -> None:
        if (not device.supports_transitions or transition.steps <= 1
                or transition.duration_sec <= 0):
            device.apply_state(target)
            return
        frames = interpolate(device.get_state(), target, transition.steps)
        pause = transition.duration_sec / len(frames)
        for frame in frames:
            device.apply_state(frame)
            time.sleep(pause)
