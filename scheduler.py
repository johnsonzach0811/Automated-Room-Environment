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
import automation
import lan

from devices import DeviceError, LightState, build_registry, default_device_name
from scenes import SceneEngine, scene_from_config
from validation import ConfigError, validate
from transport import ConnectionError, open_socket, send

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "local" / "config.json"
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
    # Existing installations can migrate without losing their saved schedule.
    path = CONFIG if CONFIG.exists() else ROOT / 'config.json'
    with path.open() as f:
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


def apply_preset(config, name, device_name=None):
    """Apply a preset to one device. Legacy contract: network failures raise
    transport.ConnectionError, exactly as before the device-layer refactor."""
    preset = config["presets"][name]
    registry = registry_for(config)
    device_name = device_name or default_device_name(config)
    device = registry.get(device_name)
    if device is None:
        raise ConfigError(f"Unknown device: {device_name!r}")
    state = preset_to_state(preset)
    device.apply_state(state)
    logging.info("Preset %s on %s: commands sent (delivery not confirmed)", name, device_name)


def apply_scene(config, name):
    """Apply a named scene across its devices. Raises DeviceError naming any
    device that failed; partial changes are possible on every target."""
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
    with automation.locked():
        if automation.read_status()['paused']:
            logging.info('Automation paused; scheduled changes skipped')
            return True
        return _check_schedules(config)


def _check_schedules(config):
    now = dt.datetime.now()
    minute = now.strftime("%Y-%m-%d %H:%M")
    STATE.parent.mkdir(parents=True, exist_ok=True)
    try:
        runs = json.loads(STATE.read_text())
    except FileNotFoundError:
        runs = {}
    except (ValueError, OSError) as exc:
        logging.error("Schedule history unreadable; no commands sent: %s", exc)
        return False
    if not isinstance(runs, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in runs.items()):
        logging.error("Invalid schedule history; no commands sent")
        return False
    failed = False
    for schedule in config["schedules"]:
        if not schedule.get("enabled", False):
            continue
        if schedule["time"] != now.strftime("%H:%M") or DAYS[now.weekday()] not in schedule["days"]:
            continue
        if dt.datetime.now().strftime("%Y-%m-%d %H:%M") != minute:
            logging.warning("Scheduled minute elapsed; remaining actions skipped")
            break
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
        write_runs(runs)
        logging.info("Schedule %s: commands sent at %s", key, minute)

    return not failed


def write_runs(runs):
    """Atomic history replacement under the shared control lock."""
    import os
    import tempfile
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=STATE.parent, delete=False) as handle:
            temporary = handle.name
            json.dump(runs, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, STATE)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["preset", "scene", "check", "validate", "pause", "resume", "status", "health"])
    parser.add_argument("name", nargs="?")
    args = parser.parse_args()
    setup_logging()
    try:
        config = None if args.action in ('pause', 'resume', 'status') else load_config()
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
    if args.action in ("pause", "resume"):
        automation.set_paused(args.action == "pause")
        print("Automation paused" if args.action == "pause" else "Automation resumed; missed schedules are not replayed")
    elif args.action == "status":
        print(json.dumps(automation.read_status()))
    elif args.action == "health":
        with automation.locked():
            for name, device in registry_for(config).items():
                if hasattr(device, "ip"):
                    resolved = lan.resolve_device(dict(ip=device.ip, port=device.port, identity=device.identity))
                    print(name, json.dumps(lan.status(resolved["ip"], device.port)))
                else:
                    print(name, "simulated; no physical hardware")
    elif args.action == "validate":
        print("Configuration valid: devices, presets, scenes, and schedules checked; no commands sent")
    elif args.action == "preset":
        if not args.name:
            raise ConfigError("preset requires a name, e.g. python3 scheduler.py preset morning")
        if args.name not in config["presets"]:
            raise ConfigError(f"Unknown preset: {args.name!r}")
        with automation.locked():
            automation.write_status(True)
            apply_preset(config, args.name)
    elif args.action == "scene":
        if not args.name:
            raise ConfigError("scene requires a name, e.g. python3 scheduler.py scene movie-night")
        if args.name not in config.get("scenes", {}):
            raise ConfigError(f"Unknown scene: {args.name!r}")
        with automation.locked():
            automation.write_status(True)
            apply_scene(config, args.name)
    else:
        if not check_schedules(config):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
