"""Config-driven Govee presets and one-shot schedule checking (Python standard library)."""
import argparse
import datetime as dt
import json
import logging
import os
import tempfile
from pathlib import Path

from validation import ConfigError, validate
from transport import ConnectionError, open_socket, send

ROOT = Path(__file__).resolve().parent
LOCAL_CONFIG = ROOT / "config.local.json"
CONFIG = LOCAL_CONFIG if LOCAL_CONFIG.exists() else ROOT / "config.json"
STATE = Path.home() / "Library" / "Application Support" / "RoomAutomation" / "last-runs.json"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
LOG = Path.home() / "Library" / "Logs" / "room-automation.log"


def setup_logging():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOG), logging.StreamHandler()],
    )


def load_config(path=None):
    with Path(path or CONFIG).open() as f:
        return validate(json.load(f))


def apply_preset(config, name):
    preset = config["presets"][name]
    device = config["device"]
    with open_socket() as sock:
        send(sock, device["ip"], device.get("port", 4003), "turn", {"value": int(preset["power"])})
        if preset["power"]:
            send(sock, device["ip"], device.get("port", 4003), "brightness", {"value": preset["brightness"]})
            send(sock, device["ip"], device.get("port", 4003), "colorwc", {
                "color": preset["color"], "colorTemInKelvin": 0
            })
    logging.info("Preset %s: commands sent to %s (delivery not confirmed)", name, device["ip"])


def check_schedules(config):
    now = dt.datetime.now()
    minute = now.strftime("%Y-%m-%d %H:%M")
    STATE.parent.mkdir(parents=True, exist_ok=True)
    try:
        runs = json.loads(STATE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        runs = {}
    if not isinstance(runs, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in runs.items()
    ):
        raise ConfigError("Schedule state must be an object of schedule names and timestamps")
    failed = False
    for schedule in config["schedules"]:
        if not schedule.get("enabled", False):
            continue
        if schedule["time"] != now.strftime("%H:%M") or DAYS[now.weekday()] not in schedule["days"]:
            continue
        key = schedule["name"]
        if runs.get(key) == minute:
            continue
        logging.info("Schedule %s due at %s; applying %s", key, minute, schedule["preset"])
        try:
            apply_preset(config, schedule["preset"])
        except ConnectionError as exc:
            logging.error("Schedule %s failed; not marked completed: %s", key, exc)
            failed = True
            continue
        runs[key] = minute
        save_state(runs)
        logging.info("Schedule %s: commands sent at %s", key, minute)

    return not failed

def save_state(runs):
    """Replace state atomically so interrupted writes cannot leave partial JSON."""
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=STATE.parent, delete=False) as f:
            temp = f.name
            json.dump(runs, f, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, STATE)
    finally:
        if temp and os.path.exists(temp):
            os.unlink(temp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["preset", "check", "validate"])
    parser.add_argument("name", nargs="?")
    parser.add_argument("--config", type=Path, default=CONFIG, help="Configuration JSON path")
    args = parser.parse_args()
    setup_logging()
    try:
        config = load_config(args.config)
        run_action(args, config)
    except (ConfigError, json.JSONDecodeError) as exc:
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
        print("Configuration valid: presets and schedules checked; no commands sent")
    elif args.action == "preset":
        if not args.name:
            raise ConfigError("preset requires a name, e.g. python3 scheduler.py preset morning")
        if args.name not in config["presets"]:
            raise ConfigError(f"Unknown preset: {args.name!r}")
        apply_preset(config, args.name)
    else:
        if not check_schedules(config):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
