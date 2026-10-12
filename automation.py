"""Persistent override and a cross-process lock shared by manual and scheduled control."""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import tempfile

ROOT = Path.home() / 'Library' / 'Application Support' / 'RoomAutomation'
STATUS = ROOT / 'automation.json'
LOCK = ROOT / 'control.lock'


@contextmanager
def locked():
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def read_status():
    try:
        data = json.loads(STATUS.read_text())
        if not isinstance(data, dict) or type(data.get('paused')) is not bool:
            raise ValueError('Invalid automation state')
        return data
    except FileNotFoundError:
        return {'paused': False}
    except (ValueError, OSError):
        # Never let a damaged override file silently resume scheduled lighting.
        return {'paused': True, 'error': 'Automation state unreadable; explicitly resume to reset it.'}


def write_status(paused):
    """Caller must hold locked(). Atomic replacement survives process restarts."""
    if type(paused) is not bool:
        raise ValueError('paused must be true or false')
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=STATUS.parent, delete=False) as handle:
            name = handle.name
            json.dump({'paused': paused}, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, STATUS)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def set_paused(paused):
    with locked():
        write_status(paused)
    return {'paused': paused}
