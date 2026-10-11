"""Validate room automation configuration before executing any lighting commands."""
import ipaddress
import re

DAYS = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}


class ConfigError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ConfigError(message)


def validate(config):
    require(isinstance(config, dict), "Configuration must be a JSON object")
    device = config.get("device")
    require(isinstance(device, dict), "device must be an object")
    ip = device.get("ip")
    try:
        ipaddress.IPv4Address(ip)
    except (ValueError, TypeError, ipaddress.AddressValueError):
        raise ConfigError("device.ip must be a valid IPv4 address") from None
    port = device.get("port", 4003)
    require(type(port) is int and 1 <= port <= 65535, "device.port must be an integer from 1 to 65535")

    presets = config.get("presets")
    require(isinstance(presets, dict) and bool(presets), "presets must be a nonempty object")
    for name, preset in presets.items():
        require(isinstance(name, str) and bool(name.strip()), "preset names must be nonempty strings")
        require(isinstance(preset, dict), f"preset {name!r} must be an object")
        require(type(preset.get("power")) is bool, f"preset {name!r}.power must be true or false")
        brightness = preset.get("brightness")
        require(type(brightness) is int and 0 <= brightness <= 100,
                f"preset {name!r}.brightness must be an integer from 0 to 100")
        color = preset.get("color")
        require(isinstance(color, dict), f"preset {name!r}.color must be an RGB object")
        for channel in ("r", "g", "b"):
            value = color.get(channel)
            require(type(value) is int and 0 <= value <= 255,
                    f"preset {name!r}.color.{channel} must be an integer from 0 to 255")

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
        require(schedule.get("preset") in presets,
                f"{prefix}.preset must reference an existing preset: {', '.join(presets)}")
    return config
