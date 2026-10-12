"""Config-driven Govee presets and one-shot schedule checking (Python standard library)."""
import argparse
import datetime as dt
import json
import logging
from pathlib import Path
import automation
import lan

from validation import ConfigError, validate
from transport import ConnectionError, open_socket, send

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "local" / "config.json"
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


def load_config():
    # Existing installations can migrate without losing their saved schedule.
    path = CONFIG if CONFIG.exists() else ROOT / 'config.json'
    with path.open() as f:
        return validate(json.load(f))


def apply_preset(config, name):
    preset = config["presets"][name]
    try:
        device = lan.resolve_device(config["device"])
    except OSError as exc:
        raise ConnectionError(str(exc)) from exc
    with open_socket() as sock:
        send(sock, device["ip"], device.get("port", 4003), "turn", {"value": int(preset["power"])})
        if preset["power"]:
            send(sock, device["ip"], device.get("port", 4003), "brightness", {"value": preset["brightness"]})
            send(sock, device["ip"], device.get("port", 4003), "colorwc", {
                "color": preset["color"], "colorTemInKelvin": 0
            })
    logging.info("Preset %s: commands sent to %s (delivery not confirmed)", name, device["ip"])


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
        logging.info("Schedule %s due at %s; applying %s", key, minute, schedule["preset"])
        try:
            apply_preset(config, schedule["preset"])
        except ConnectionError as exc:
            logging.error("Schedule %s failed; not marked completed: %s", key, exc)
            failed = True
            continue
        runs[key] = minute
        STATE.write_text(json.dumps(runs, indent=2) + "\n")
        logging.info("Schedule %s: commands sent at %s", key, minute)

    return not failed

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["preset", "check", "validate", "pause", "resume", "status"])
    parser.add_argument("name", nargs="?")
    args = parser.parse_args()
    setup_logging()
    try:
        config = None if args.action in ('pause', 'resume', 'status') else load_config()
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
    if args.action in ('pause', 'resume'):
        automation.set_paused(args.action == 'pause')
        print('Automation paused' if args.action == 'pause' else 'Automation resumed; missed schedules are not replayed')
    elif args.action == 'status':
        print(json.dumps(automation.read_status()))
    elif args.action == "validate":
        print("Configuration valid: presets and schedules checked; no commands sent")
    elif args.action == "preset":
        if not args.name:
            raise ConfigError("preset requires a name, e.g. python3 scheduler.py preset morning")
        if args.name not in config["presets"]:
            raise ConfigError(f"Unknown preset: {args.name!r}")
        with automation.locked():
            automation.write_status(True)
            apply_preset(config, args.name)
    else:
        if not check_schedules(config):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
