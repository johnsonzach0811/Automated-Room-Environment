"""Basic local Govee LAN light control for the H619D."""
import argparse
import logging

from scheduler import CONFIG, load_config
from validation import ConfigError
from transport import ConnectionError, open_socket, send as send_command

def send(sock, command, data, device):
    send_command(sock, device["ip"], device.get("port", 4003), command, data)

def main():
    parser = argparse.ArgumentParser(description="Control Govee lights over LAN")
    parser.add_argument("action", choices=["on", "off"])
    parser.add_argument("--config", default=CONFIG, help="Configuration JSON path")
    args = parser.parse_args()
    device = load_config(args.config)["device"]
    with open_socket() as sock:
        if args.action == "off":
            send(sock, "turn", {"value": 0}, device)
        else:
            send(sock, "turn", {"value": 1}, device)
            send(sock, "brightness", {"value": 30}, device)
            send(sock, "colorwc", {
                "color": {"r": 255, "g": 210, "b": 160},
                "colorTemInKelvin": 0,
            }, device)
    print(f"Sent {args.action} command to {device['ip']} (delivery not confirmed)")

if __name__ == "__main__":
    try:
        main()
    except (ConnectionError, ConfigError, OSError, ValueError) as exc:
        logging.error("Lighting connection failed: %s", exc)
        raise SystemExit(1) from None
