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
    from devices import LightState, default_device_name
    config = scheduler.load_config()
    with automation.locked():
        automation.write_status(True)
        light = scheduler.registry_for(config)[default_device_name(config)]
        light.apply_state(LightState(power=args.action == "on", brightness=30,
                                    color=(255, 210, 160)))
    print(f"Sent {args.action} command (delivery not confirmed). Automation paused until resumed.")

if __name__ == "__main__":
    try:
        main()
    except ConnectionError as exc:
        logging.error("Lighting connection failed: %s", exc)
        raise SystemExit(1) from None
