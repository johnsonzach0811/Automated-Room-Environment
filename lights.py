"""Basic local Govee LAN light control for the H619D."""
import argparse
import logging

from transport import ConnectionError, open_socket, send as send_command

LIGHT_IP = "192.168.4.29"
PORT = 4003

def send(sock, command, data):
    send_command(sock, LIGHT_IP, PORT, command, data)

def main():
    parser = argparse.ArgumentParser(description="Control Govee lights over LAN")
    parser.add_argument("action", choices=["on", "off"])
    args = parser.parse_args()
    with open_socket() as sock:
        if args.action == "off":
            send(sock, "turn", {"value": 0})
        else:
            send(sock, "turn", {"value": 1})
            send(sock, "brightness", {"value": 30})
            send(sock, "colorwc", {
                "color": {"r": 255, "g": 210, "b": 160},
                "colorTemInKelvin": 0,
            })
    print(f"Sent {args.action} command to {LIGHT_IP} (delivery not confirmed)")

if __name__ == "__main__":
    try:
        main()
    except ConnectionError as exc:
        logging.error("Lighting connection failed: %s", exc)
        raise SystemExit(1) from None
