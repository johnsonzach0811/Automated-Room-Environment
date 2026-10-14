# Project Muse

Local room atmosphere automation using Python's standard library. Govee H619D
power, brightness, RGB, and two unattended lighting tests have recorded hardware
evidence. This integration combines the lighting override/install improvements
with named devices and scenes. It does not complete M1 or Phase A.

The last recorded regular morning check (October 12) was skipped because automation
was paused. Physical morning activation, restart/login, sleep/wake, and offline
recovery remain unverified. See [current verification](docs/verification-2026-10-13.md).

## Setup

Requires Python 3.10+; no packages required. Enable LAN Control for the H619D.
From a stable checkout:

```sh
mkdir -p local
cp config.example.json local/config.json
# Edit only local/config.json with your device details.
python3 -B scheduler.py validate
python3 -B dashboard.py
```

Open http://127.0.0.1:8765 on this Mac. A fresh example has scheduling disabled.
Existing private configuration and pause state are preserved during installation.
See [installation and recovery](docs/installation.md) for the preview/apply installer.

## Devices, presets, and scenes

Legacy `device` configuration remains supported as device `default`. A `devices`
list contains named `govee` or `simulated` entries. No legacy device is synthesized.
`default_device` selects the device for preset and individual dashboard controls;
otherwise the legacy device or first list entry is selected. Defining both a legacy
device and a list entry named `default` is rejected.

Scenes map configured device names to desired power, brightness, and RGB settings.
Omitted scene settings default to on, 100%, and white; they do not preserve hardware
settings. Schedules reference exactly one `preset` or `scene`. The dashboard can
apply named scenes and edit either kind of schedule while preserving definitions.
Scene definitions are edited in local configuration; a scene editor is not included.

See [a safe simulated configuration](docs/scenes-example.json). Simulated devices
keep state only within a process and do not establish physical compatibility.
Govee scene targets apply directly: fades are disabled because fresh adapters do
not know actual hardware state. Simulated transitions accept finite durations of
0–30 seconds and 1–60 steps, accounting for command time. Targets run sequentially;
scenes are not synchronized or atomic across devices.

## Commands

```sh
python3 -B scheduler.py validate       # no device commands
python3 -B scheduler.py status         # persisted pause state
python3 -B scheduler.py pause
python3 -B scheduler.py resume         # future schedules only
python3 -B scheduler.py preset morning
python3 -B scheduler.py scene autumn
python3 -B scheduler.py health         # read-only discovery/device status
python3 -B scheduler.py check          # one schedule check
python3 -B lights.py off
```

Manual presets, scenes, and individual controls persistently pause automation before
sending. Resume explicitly when future routines should run. The dashboard shows
desired controls, not continuously polled hardware state. UDP send success does
not confirm delivery. `health` explicitly queries hardware without changing lights
or pause state; an unavailable device makes the command fail.

## Scheduling and testing

One macOS LaunchAgent invokes a one-shot check every minute. It requires an awake
Mac and logged-in GUI session. Missed minutes are skipped, including paused minutes;
resuming does not replay them. A shared process lock and atomically replaced run
history prevent concurrent controls and duplicate successful checks in a minute.
See [reliability limits](RELIABILITY.md) and [the dashboard guide](docs/local-dashboard.md).

```sh
python3 -B -m unittest discover -s tests -v
```

Tests use temporary files, mocked LAN commands, and a temporary localhost HTTP
server. They do not change installed jobs or physical lights.

## Project scope

TV/audio compatibility, three autumn scenes, architecture decisions, and the
Phase A verification executions remain pending. M1 target: October 16, 2026;
Phase A target: November 20, 2026. [Charter](docs/project-charter.md),
[scope](docs/scope-statement.md), [work packages](docs/m1-work-packages.md), and
[roadmap](docs/roadmap.md) describe the remaining work. Historic records retain
their original evidence; the newest verification record describes this integration.

Keep device identities, addresses, credentials, and backups in ignored `local/`.
No open-source license has been selected.
