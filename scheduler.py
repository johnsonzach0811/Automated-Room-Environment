"""Config-driven presets, scenes, and one-shot schedule checking (Python standard library).

Scheduling model is unchanged: launchd invokes `scheduler.py check` every
minute; due schedules are applied once per minute and recorded in the state
file, so retries within the same minute are idempotent and there is no late
catch-up. See RELIABILITY.md.
"""
import argparse
import datetime as dt
import json
import logging
from pathlib import Path

from devices import DeviceError, LightState, build_registry
from scenes import SceneEngine, scene_from_config
from validation import ConfigError, validate
from transport import ConnectionError, open_socket, send

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config.json"
STATE = Path.home() / "Library" / "Application Support" / "RoomAutomation" / "last-runs.json"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
LOG = Path.home() / "Library" / "Logs" / "room-automation.log"

# Devices that fail to apply; launchd-visible failures stay loud.
DEVICE_FAILURES = (ConnectionError, DeviceError)


def setup_logging():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.FileHandler(LOG), logging.StreamHandler()],
    )


def load_config():
    with CONFIG.open() as f:
        return validate(json.load(f))


def registry_for(config):
    """Device registry wired to this module's transport seams.

    open_socket/send are looked up on this module at call time so tests can
    patch scheduler.open_socket and scheduler.send.
    """
    return build_registry(config, socket_factory=open_socket, sender=send)


def preset_to_state(preset):
    color = preset.get("color", {"r": 255, "g": 255, "b": 255})
    return LightState(
        power=preset["power"],
        brightness=preset["brightness"],
        color=(color["r"], color["g"], color["b"]),
    )


def apply_preset(config, name, device_name="default"):
    """Apply a preset to one device. Legacy contract: network failures raise
    transport.ConnectionError, exactly as before the device-layer refactor."""
    preset = config["presets"][name]
    registry = registry_for(config)
    device = registry.get(device_name)
    if device is None:
        raise ConfigError(f"Unknown device: {device_name!r}")
    state = preset_to_state(preset)
    device.apply_state(state)
    logging.info("Preset %s on %s: commands sent (delivery not confirmed)", name, device_name)


def apply_scene(config, name):
    """Apply a named scene across its devices. Raises DeviceError naming any
    device that failed; scenes are all-or-nothing per device, not atomic."""
    raw = config.get("scenes", {}).get(name)
    if raw is None:
        raise ConfigError(f"Unknown scene: {name!r}")
    scene = scene_from_config(name, raw)
    engine = SceneEngine(registry_for(config))
    engine.apply(scene)


def apply_schedule_target(config, schedule):
    if "scene" in schedule:
        apply_scene(config, schedule["scene"])
    else:
        apply_preset(config, schedule["preset"])


def check_schedules(config):
    now = dt.datetime.now()
    minute = now.strftime("%Y-%m-%d %H:%M")
    STATE.parent.mkdir(parents=True, exist_ok=True)
    try:
        runs = json.loads(STATE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        runs = {}
    failed = False
    for schedule in config["schedules"]:
        if not schedule.get("enabled", False):
            continue
        if schedule["time"] != now.strftime("%H:%M") or DAYS[now.weekday()] not in schedule["days"]:
            continue
        key = schedule["name"]
        if runs.get(key) == minute:
            continue
        target = schedule.get("scene") or schedule.get("preset")
        logging.info("Schedule %s due at %s; applying %s", key, minute, target)
        try:
            apply_schedule_target(config, schedule)
        except DEVICE_FAILURES as exc:
            logging.error("Schedule %s failed; not marked completed: %s", key, exc)
            failed = True
            continue
        runs[key] = minute
        STATE.write_text(json.dumps(runs, indent=2) + "\n")
        logging.info("Schedule %s: commands sent at %s", key, minute)

    return not failed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["preset", "scene", "check", "validate"])
    parser.add_argument("name", nargs="?")
    args = parser.parse_args()
    setup_logging()
    try:
        config = load_config()
        run_action(args, config)
    except (ConfigError, DeviceError, json.JSONDecodeError) as exc:
        logging.error("Invalid configuration: %s", exc)
        raise SystemExit(1) from None
    except ConnectionError as exc:
        logging.error("Lighting connection failed: %s", exc)
        raise SystemExit(1) from None
    except Exception:
        logging.exception("Automation failed")
        raise


def run_action(args, config):
    if args.action == "validate":
        print("Configuration valid: devices, presets, scenes, and schedules checked; no commands sent")
    elif args.action == "preset":
        if not args.name:
            raise ConfigError("preset requires a name, e.g. python3 scheduler.py preset morning")
        if args.name not in config["presets"]:
            raise ConfigError(f"Unknown preset: {args.name!r}")
        apply_preset(config, args.name)
    elif args.action == "scene":
        if not args.name:
            raise ConfigError("scene requires a name, e.g. python3 scheduler.py scene movie-night")
        apply_scene(config, args.name)
    else:
        if not check_schedules(config):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
