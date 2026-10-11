"""Basic local Govee LAN light control for the H619D.

Legacy entry point; now delegates to the devices package. Behavior is
unchanged: `on` powers the strip and applies the warm 30% preset, `off`
powers it down.
"""
import argparse
import logging

from devices import GoveeLight, DeviceError
from transport import ConnectionError, open_socket, send as send_command

LIGHT_IP = "192.168.4.29"
PORT = 4003


def send(sock, command, data):
    send_command(sock, LIGHT_IP, PORT, command, data)


def build_light():
    return GoveeLight("legacy", LIGHT_IP, PORT)


def main():
    from devices.base import LightState
    parser = argparse.ArgumentParser(description="Control Govee lights over LAN")
    parser.add_argument("action", choices=["on", "off"])
    args = parser.parse_args()
    light = build_light()
    if args.action == "off":
        light.apply_state(LightState(power=False))
    else:
        light.apply_state(LightState(power=True, brightness=30, color=(255, 210, 160)))
    print(f"Sent {args.action} command to {LIGHT_IP} (delivery not confirmed)")


if __name__ == "__main__":
    try:
        main()
    except (ConnectionError, DeviceError) as exc:
        logging.error("Lighting connection failed: %s", exc)
        raise SystemExit(1) from None
