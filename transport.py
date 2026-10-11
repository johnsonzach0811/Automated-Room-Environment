"""Bounded UDP sends; success means locally sent, not device acknowledgement."""
import json
import logging
import socket
import time


class ConnectionError(OSError):
    """The operating system could not send a lighting command."""


def open_socket():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.settimeout(2.0)
        except OSError:
            sock.close()
            raise
        return sock
    except OSError as exc:
        raise ConnectionError(f"Could not initialize lighting socket: {exc}") from exc


def send(sock, ip, port, cmd, data):
    payload = json.dumps({"msg": {"cmd": cmd, "data": data}}).encode()
    for attempt in range(1, 4):
        try:
            sent = sock.sendto(payload, (ip, port))
            if sent != len(payload):
                raise OSError("Incomplete UDP send")
        except OSError as exc:
            logging.warning("Command %s to %s:%s failed (attempt %s/3): %s",
                            cmd, ip, port, attempt, exc)
            if attempt == 3:
                raise ConnectionError(
                    f"Command {cmd} to {ip}:{port} failed after 3 attempts: {exc}"
                ) from exc
            time.sleep(attempt)
        else:
            time.sleep(0.3)
            return
