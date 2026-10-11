# Project Muse

Mac-based room lighting automation for a Govee H619D. A working lighting prototype is implemented: local controls, Morning and Focus presets, configurable schedules, a browser dashboard, retries, and persistent pause/resume. The broader seasonal room project remains in Phase A; TV/audio integration and the three autumn scenes are pending a joint scope decision.

## Setup

Requires macOS and Python 3.9+; only the standard library is used.

```sh
mkdir -p local
cp config.example.json local/config.json
# Set your Govee device address in local/config.json; enable LAN Control in Govee Home.
python3 -B scheduler.py validate
python3 -B scripts/discover_light.py
# Pair the exact identity printed above; future controls resolve its current address.
python3 -B scripts/discover_light.py --update --device-id YOUR_DEVICE_ID
python3 -B scripts/install_launchd.py
# Review the preview, then install one scheduler owner:
python3 -B scripts/install_launchd.py --apply
python3 -B dashboard.py
```

Open http://127.0.0.1:8765 on this Mac. The dashboard runs while its process stays open; the LaunchAgent schedules work independently. Manual controls pause automation until you explicitly resume it in the dashboard or with `python3 -B scheduler.py resume`. Pause persists across dashboard and scheduler restarts.

New example schedules are disabled. Existing installations keep their saved configuration, including the enabled Monday–Thursday 06:45 Morning routine. The installer backs up configuration and prior LaunchAgents, retires the legacy morning and known temporary test jobs, and installs the configurable scheduler. It sends no immediate lighting commands.

## Architecture and limits

`launchd` → `scheduler.py check` → Govee LAN UDP. `dashboard.py` provides loopback-only HTTP controls and schedule editing. `automation.py` shares an on-disk pause state and a cross-process lock between manual and scheduled actions. `lan.py` provides discovery and explicit status reads. Once paired, controls discover the exact device identity before sending; discovery failure prevents a command to an unverified DHCP address.

Schedules use the Mac's local clock and run only in their matching minute. No late catch-up occurs. The Mac must be awake and logged in. Sending UDP does not confirm delivery; physical verification uses a separate status query or observation. Manual changes pause before sending, including on a send failure. Pause waits for any already-running control to finish, then prevents subsequent scheduled changes. Resume does not immediately alter the lights.

## Verification and project status

```sh
python3 -B -m unittest discover -s tests -v
python3 -B scheduler.py validate
python3 -B scheduler.py status
```

Tests use temporary state and mocked lighting commands. See [October 11 verification](docs/verification-2026-10-11.md), [dashboard use](docs/local-dashboard.md), [installation and recovery](docs/installation.md), and [reliability](RELIABILITY.md).

The recovered `feature/modular-scenes` branch is available in a separate draft PR. Its five commits and 63 tests are preserved. It is not deployed: device routing, dashboard scene-schedule editing, and transition semantics need correction before integration.

The [charter](docs/project-charter.md) still requires two device categories, three autumn scenes, pause/override verification, and 30 observed end-to-end executions (including 10 scheduled). M1 target is October 16; Phase A target is November 20, with a 36-hour effort ceiling. No phase gate is claimed complete.

## Local configuration

`local/config.json` holds home addresses and paired identity and is ignored by Git. The legacy root `config.json` remains a read fallback for existing installations; migrate using the installer. Only a disabled example using a documentation-only address is published. Earlier commits contained a private LAN address; this update removes it from current files without rewriting repository history. No open-source license has been selected.
