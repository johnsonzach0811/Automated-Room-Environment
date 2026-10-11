"""Bounded UDP sends; success means locally sent, not device acknowledgement.

Network behavior is explicit and configurable, with defaults matching the
original implementation: 2s socket timeout, up to 3 attempts, 1s then 2s
retry backoff, 0.3s spacing between commands.
"""
import json
import logging
import socket
import time

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SEC = 2.0
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_BASE_SEC = 1.0
DEFAULT_SPACING_SEC = 0.3


class ConnectionError(OSError):
    """The operating system could not send a lighting command."""


def open_socket(timeout_sec=DEFAULT_TIMEOUT_SEC):
    """Create a UDP socket with a send timeout.

    Raises ConnectionError when the socket cannot be created or the timeout
    cannot be applied; a half-configured socket is always closed.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except OSError as exc:
        raise ConnectionError(f"Could not initialize lighting socket: {exc}") from exc
    try:
        sock.settimeout(timeout_sec)
    except OSError as exc:
        sock.close()
        raise ConnectionError(f"Could not set socket timeout: {exc}") from exc
    return sock


def send(sock, ip, port, cmd, data, retries=DEFAULT_RETRIES,
         backoff_base_sec=DEFAULT_BACKOFF_BASE_SEC, spacing_sec=DEFAULT_SPACING_SEC):
    """Send one command datagram, retrying transient OS errors.

    Raises ConnectionError after `retries` exhausted attempts. Success means
    the OS accepted the datagram; an offline UDP destination may produce no
    error at all.
    """
    if retries < 1:
        raise ConnectionError(f"Command {cmd} to {ip}:{port}: retries must be >= 1")
    payload = json.dumps({"msg": {"cmd": cmd, "data": data}}).encode()
    for attempt in range(1, retries + 1):
        try:
            sent = sock.sendto(payload, (ip, port))
            if sent != len(payload):
                raise OSError("Incomplete UDP send")
        except OSError as exc:
            log.warning("Command %s to %s:%s failed (attempt %s/%s): %s",
                        cmd, ip, port, attempt, retries, exc)
            if attempt == retries:
                raise ConnectionError(
                    f"Command {cmd} to {ip}:{port} failed after {retries} attempts: {exc}"
                ) from exc
            time.sleep(backoff_base_sec * attempt)
        else:
            time.sleep(spacing_sec)
            return
