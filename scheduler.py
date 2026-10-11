"""Config-driven Govee presets and one-shot schedule checking (Python standard library)."""
import argparse
import datetime as dt
import json
import socket
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config.json"
STATE = Path.home() / "Library" / "Application Support" / "RoomAutomation" / "last-runs.json"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def load_config():
    with CONFIG.open() as f:
        return json.load(f)


def send(sock, ip, port, cmd, data):
    payload = json.dumps({"msg": {"cmd": cmd, "data": data}}).encode()
    for attempt in range(3):
        try:
            sock.sendto(payload, (ip, port))
            time.sleep(0.3)
            return
        except OSError:
            if attempt == 2:
                raise
            time.sleep(1)


def apply_preset(config, name):
    preset = config["presets"][name]
    device = config["device"]
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        send(sock, device["ip"], device.get("port", 4003), "turn", {"value": int(preset["power"])})
        if preset["power"]:
            send(sock, device["ip"], device.get("port", 4003), "brightness", {"value": preset["brightness"]})
            send(sock, device["ip"], device.get("port", 4003), "colorwc", {
                "color": preset["color"], "colorTemInKelvin": 0
            })
    print(f"Applied preset: {name}")


def check_schedules(config):
    now = dt.datetime.now()
    minute = now.strftime("%Y-%m-%d %H:%M")
    STATE.parent.mkdir(parents=True, exist_ok=True)
    try:
        runs = json.loads(STATE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        runs = {}
    for schedule in config["schedules"]:
        if not schedule.get("enabled", False):
            continue
        if schedule["time"] != now.strftime("%H:%M") or DAYS[now.weekday()] not in schedule["days"]:
            continue
        key = schedule["name"]
        if runs.get(key) == minute:
            continue
        apply_preset(config, schedule["preset"])
        runs[key] = minute
        STATE.write_text(json.dumps(runs, indent=2) + "\n")
        print(f"Schedule fired: {key} at {minute}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["preset", "check"])
    parser.add_argument("name", nargs="?")
    args = parser.parse_args()
    config = load_config()
    if args.action == "preset":
        if not args.name:
            parser.error("preset requires a name, e.g. python3 scheduler.py preset morning")
        apply_preset(config, args.name)
    else:
        check_schedules(config)


if __name__ == "__main__":
    main()
