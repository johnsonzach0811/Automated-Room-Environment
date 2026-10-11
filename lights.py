"""Basic local Govee LAN light control for the H619D."""
import argparse
import json
import socket
import time

LIGHT_IP = "192.168.4.29"
PORT = 4003

def send(sock, command, data):
    packet = {"msg": {"cmd": command, "data": data}}
    sock.sendto(json.dumps(packet).encode(), (LIGHT_IP, PORT))
    time.sleep(0.3)

def main():
    parser = argparse.ArgumentParser(description="Control Govee lights over LAN")
    parser.add_argument("action", choices=["on", "off"])
    args = parser.parse_args()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        if args.action == "off":
            send(sock, "turn", {"value": 0})
        else:
            send(sock, "turn", {"value": 1})
            send(sock, "brightness", {"value": 30})
            send(sock, "colorwc", {
                "color": {"r": 255, "g": 210, "b": 160},
                "colorTemInKelvin": 0,
            })
    print(f"Sent {args.action} command to {LIGHT_IP}")

if __name__ == "__main__":
    main()
