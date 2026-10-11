# Project Muse

Home atmosphere automation — seasonal room control that will grow into the
Muse platform (lighting, TVs, speakers, and other connected devices driven
by schedules, presets, and natural-language commands).

Status: modular Python foundation on `main`'s successor branch. Govee H619D
LAN control is proven on the owner's network; the codebase now supports
multiple device types, named scenes with transitions, simulated devices,
and 63 automated tests. See [the roadmap](docs/roadmap.md) for what comes
next.

## Architecture

```
config.json ──▶ validation.py ──▶ scheduler.py ──▶ scenes.py ──▶ devices/
  (devices,        (strict schema,    (CLI: preset /       (named scenes,    (Device ABC,
   presets,        legacy "device"     scene / check /       transitions,     GoveeLight LAN,
   scenes,        key synthesized)    validate)             per-device       SimulatedLight)
   schedules)  ──▶ dashboard.py ──▶  outcomes)
                   (loopback-only
                    local UI)

transport.py — bounded UDP sends shared by every LAN device
lights.py    — legacy on/off CLI (delegates to devices/)
```

- **devices/**: `Device` abstract base class plus a `LightState`
  (power/brightness/RGB). `GoveeLight` speaks the Govee LAN API over UDP
  (port 4003); `SimulatedLight` is an in-memory stand-in for tests and
  development. New hardware = new subclass + one registry entry.
- **scenes.py**: named scenes map device names to states, with optional
  transitions (linear brightness/color fades over N steps). Failures are
  recorded per device; one unreachable light never aborts the rest.
- **scheduler.py**: config-driven presets and one-shot schedule checks.
  Launchd invokes `scheduler.py check` each minute; due schedules run once
  per minute (idempotent via a state file) with no late catch-up.
- **transport.py**: UDP with 2s timeout, 3 attempts, 1s/2s backoff, 0.3s
  spacing — all configurable per call. Success means the OS accepted a
  datagram, never device acknowledgement (UDP is one-way).
- **dashboard.py**: loopback-only local web UI (127.0.0.1:8765) for presets,
  manual control, and schedule editing.

Standard library only — no dependencies to install.

## Installation

Requires Python 3.10+ (developed against 3.12/3.14).

```bash
git clone https://github.com/johnsonzach0811/automated-room-environment.git
cd automated-room-environment
cp config.example.json config.json   # then edit device IPs
```

Enable **LAN Control** for each Govee device in the Govee Home app
(Device settings → LAN Control). No cloud account, API keys, or pairing
tokens are used or stored.

## Configuration

Two formats are accepted (validated strictly before anything runs):

**Legacy** — single light, as before:
```json
{"device": {"ip": "192.168.4.29", "port": 4003}, "presets": {...}, "schedules": [...]}
```

**Multi-device** — named devices plus scenes:
```json
{
  "devices": [
    {"name": "desk-strip", "type": "govee", "ip": "192.168.4.29"},
    {"name": "shelf-strip", "type": "govee", "ip": "192.168.4.30"},
    {"name": "virtual-test", "type": "simulated"}
  ],
  "scenes": {
    "movie-night": {
      "devices": {
        "desk-strip": {"power": true, "brightness": 15,
                       "color": {"r": 255, "g": 80, "b": 20}},
        "shelf-strip": {"power": false}
      },
      "transition": {"duration_sec": 5.0, "steps": 10}
    }
  },
  "schedules": [
    {"name": "Friday wind-down", "enabled": true, "time": "21:30",
     "days": ["Fri"], "scene": "movie-night"}
  ]
}
```

Each schedule references exactly one `preset` or `scene`. See
`config.example.json` for a complete working example.

## Usage

```bash
# Validate configuration (sends nothing)
python3 -B scheduler.py validate

# Apply a preset to the default device
python3 -B scheduler.py preset morning

# Apply a scene across devices
python3 -B scheduler.py scene movie-night

# Check due schedules once (what launchd runs every minute)
python3 -B scheduler.py check

# Legacy on/off CLI
python3 -B lights.py on|off

# Local dashboard (loopback only)
python3 -B dashboard.py   # → http://127.0.0.1:8765
```

## Simulated devices and tests

`simulated` devices behave like real lights without touching the network —
use them to develop scenes and schedules anywhere:

```python
from devices import SimulatedLight, LightState
light = SimulatedLight("desk")
light.apply_state(LightState(power=True, brightness=40, color=(255, 200, 150)))
light.fail_next()  # inject a failure to test error paths
```

Run the suite (no hardware or network required):

```bash
python3 -B -m unittest discover -s tests -v
```

## Scheduling on macOS

The existing launchd job calls `scheduler.py check` every minute. That model
is intentionally unchanged: one-shot checks, per-minute idempotency via
`~/Library/Application Support/RoomAutomation/last-runs.json`, no daemon,
no catch-up for missed minutes. Logs go to
`~/Library/Logs/room-automation.log`. See [RELIABILITY.md](RELIABILITY.md)
and [docs/local-dashboard.md](docs/local-dashboard.md).

## Repository hygiene

Keep API keys, pairing tokens, personal media files, and home
network/device details out of commits. Use `.env.example` or redacted
configuration if code is introduced. No open-source license has been
selected.

## Docs

- [Project charter](docs/project-charter.md) and [scope statement](docs/scope-statement.md)
- [Roadmap to the Muse MVP](docs/roadmap.md)
- [M1 work packages](docs/m1-work-packages.md) (M1 target: October 16, 2026)
- [Progress record, 2026-10-10](docs/progress-2026-10-10.md)
- Templates live in `templates/`
