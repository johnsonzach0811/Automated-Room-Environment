"""Basic local Govee LAN light control for the H619D."""
import argparse
import logging
import automation
import scheduler
import lan

from transport import ConnectionError, open_socket, send as send_command

def send(sock, command, data, device=None):
    device = device or lan.resolve_device(scheduler.load_config()['device'])
    send_command(sock, device['ip'], device.get('port', 4003), command, data)

def main():
    parser = argparse.ArgumentParser(description="Control Govee lights over LAN")
    parser.add_argument("action", choices=["on", "off"])
    args = parser.parse_args()
    device = lan.resolve_device(scheduler.load_config()['device'])
    with automation.locked(), open_socket() as sock:
        automation.write_status(True)
        if args.action == "off":
            send(sock, "turn", {"value": 0}, device)
        else:
            send(sock, "turn", {"value": 1}, device)
            send(sock, "brightness", {"value": 30}, device)
            send(sock, "colorwc", {
                "color": {"r": 255, "g": 210, "b": 160},
                "colorTemInKelvin": 0,
            }, device)
    print(f"Sent {args.action} command (delivery not confirmed). Automation paused until resumed.")

if __name__ == "__main__":
    try:
        main()
    except ConnectionError as exc:
        logging.error("Lighting connection failed: %s", exc)
        raise SystemExit(1) from None
