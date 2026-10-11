"""Validate room automation configuration before executing any lighting commands."""
import ipaddress
import numbers
import re

from devices import DEVICE_TYPES

DAYS = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}


class ConfigError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ConfigError(message)


def validate_ipv4(value, message):
    try:
        ipaddress.IPv4Address(value)
    except (ValueError, TypeError, ipaddress.AddressValueError):
        raise ConfigError(message) from None


def validate_port(port, message):
    require(type(port) is int and 1 <= port <= 65535, message)


def validate_color(color, prefix):
    require(isinstance(color, dict), f"{prefix}.color must be an RGB object")
    for channel in ("r", "g", "b"):
        value = color.get(channel)
        require(type(value) is int and 0 <= value <= 255,
                f"{prefix}.color.{channel} must be an integer from 0 to 255")


def validate_device_entry(entry, index, names):
    prefix = f"devices[{index}]"
    require(isinstance(entry, dict), f"{prefix} must be an object")
    name = entry.get("name")
    require(isinstance(name, str) and bool(name.strip()), f"{prefix}.name must be a nonempty string")
    require(name not in names, f"Duplicate device name: {name!r}")
    names.add(name)
    dtype = entry.get("type", "govee")
    require(dtype in DEVICE_TYPES,
            f"{prefix}.type must be one of: {', '.join(sorted(DEVICE_TYPES))}")
    if dtype == "govee":
        validate_ipv4(entry.get("ip"), f"{prefix}.ip must be a valid IPv4 address")
    elif "ip" in entry:
        validate_ipv4(entry.get("ip"), f"{prefix}.ip must be a valid IPv4 address")
    validate_port(entry.get("port", 4003), f"{prefix}.port must be an integer from 1 to 65535")


def validate_devices(config):
    """Validate device configuration; returns the set of known device names.

    Accepts the legacy single "device" object, the new "devices" list, or
    both. When only "devices" is present, a legacy-compatible "device" entry
    is synthesized from the first device so existing consumers keep working.
    """
    names = set()
    if "devices" in config:
        devices = config["devices"]
        require(isinstance(devices, list) and bool(devices), "devices must be a nonempty list")
        for index, entry in enumerate(devices):
            validate_device_entry(entry, index, names)
    if "device" in config:
        device = config["device"]
        require(isinstance(device, dict), "device must be an object")
        validate_ipv4(device.get("ip"), "device.ip must be a valid IPv4 address")
        validate_port(device.get("port", 4003), "device.port must be an integer from 1 to 65535")
        names.add("default")
    require(bool(names), 'Configuration must define "device" or a nonempty "devices" list')
    if "devices" in config and "device" not in config:
        first = config["devices"][0]
        config["device"] = {"ip": first.get("ip", "127.0.0.1"),
                            "port": first.get("port", 4003)}
    return names


def validate_scene_settings(settings, prefix):
    require(isinstance(settings, dict), f"{prefix} must be an object")
    require(set(settings) <= {"power", "brightness", "color"},
            f"{prefix} allows only power, brightness, color")
    if "power" in settings:
        require(type(settings["power"]) is bool, f"{prefix}.power must be true or false")
    if "brightness" in settings:
        require(type(settings["brightness"]) is int and 0 <= settings["brightness"] <= 100,
                f"{prefix}.brightness must be an integer from 0 to 100")
    if "color" in settings:
        validate_color(settings["color"], prefix)


def validate_scenes(config, device_names):
    scenes = config.get("scenes", {})
    require(isinstance(scenes, dict), "scenes must be an object")
    for name, scene in scenes.items():
        require(isinstance(name, str) and bool(name.strip()), "scene names must be nonempty strings")
        require(isinstance(scene, dict), f"scene {name!r} must be an object")
        targets = scene.get("devices")
        require(isinstance(targets, dict) and bool(targets),
                f"scene {name!r}.devices must be a nonempty object")
        for device_name, settings in targets.items():
            require(device_name in device_names,
                    f"scene {name!r} references unknown device {device_name!r}")
            validate_scene_settings(settings, f"scene {name!r}.devices[{device_name}]")
        if "transition" in scene:
            transition = scene["transition"]
            require(isinstance(transition, dict), f"scene {name!r}.transition must be an object")
            duration = transition.get("duration_sec", 0.0)
            require(isinstance(duration, numbers.Real) and not isinstance(duration, bool)
                    and duration >= 0,
                    f"scene {name!r}.transition.duration_sec must be a number >= 0")
            steps = transition.get("steps", 1)
            require(type(steps) is int and steps >= 1,
                    f"scene {name!r}.transition.steps must be an integer >= 1")


def validate(config):
    require(isinstance(config, dict), "Configuration must be a JSON object")
    device_names = validate_devices(config)

    presets = config.get("presets")
    require(isinstance(presets, dict) and bool(presets), "presets must be a nonempty object")
    for name, preset in presets.items():
        require(isinstance(name, str) and bool(name.strip()), "preset names must be nonempty strings")
        require(isinstance(preset, dict), f"preset {name!r} must be an object")
        require(type(preset.get("power")) is bool, f"preset {name!r}.power must be true or false")
        brightness = preset.get("brightness")
        require(type(brightness) is int and 0 <= brightness <= 100,
                f"preset {name!r}.brightness must be an integer from 0 to 100")
        validate_color(preset.get("color"), f"preset {name!r}")

    validate_scenes(config, device_names)

    schedules = config.get("schedules")
    require(isinstance(schedules, list), "schedules must be a list")
    names = set()
    for index, schedule in enumerate(schedules):
        prefix = f"schedules[{index}]"
        require(isinstance(schedule, dict), f"{prefix} must be an object")
        name = schedule.get("name")
        require(isinstance(name, str) and bool(name.strip()), f"{prefix}.name must be a nonempty string")
        require(name not in names, f"Duplicate schedule name: {name!r}")
        names.add(name)
        require(type(schedule.get("enabled")) is bool, f"{prefix}.enabled must be true or false")
        value = schedule.get("time")
        require(isinstance(value, str) and re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", value) is not None,
                f"{prefix}.time must use 24-hour HH:MM (e.g. 06:45)")
        days = schedule.get("days")
        require(isinstance(days, list) and bool(days) and all(isinstance(day, str) and day in DAYS for day in days),
                f"{prefix}.days must be a nonempty list of Mon, Tue, Wed, Thu, Fri, Sat, Sun")
        require(len(days) == len(set(days)), f"{prefix}.days contains duplicates")
        has_preset = "preset" in schedule
        has_scene = "scene" in schedule
        require(has_preset != has_scene,
                f"{prefix} must reference exactly one of preset or scene")
        if has_preset:
            require(isinstance(schedule.get("preset"), str) and schedule.get("preset") in presets,
                    f"{prefix}.preset must reference an existing preset: {', '.join(presets)}")
        else:
            require(isinstance(schedule.get("scene"), str) and schedule.get("scene") in config.get("scenes", {}),
                    f"{prefix}.scene must reference an existing scene")
    return config
