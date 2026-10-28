# Configurable lighting automation

Current implementation: `scheduler.py` reads validated JSON, applies named presets, and checks enabled schedules. This file supersedes the initial disabled-weekday-only setup notes.

## Configuration

Copy the tracked example `config.json` to ignored `config.local.json`. Set the device IP there and test `morning`, `focus`, and `night` manually before enabling schedules. The example retains a daily wake/daytime/progressive-evening/night pattern, with **all schedules disabled**. `config.local.json` takes precedence automatically; `--config` selects an explicit file.

```sh
python3 -B scheduler.py validate
python3 -B scheduler.py preset morning
python3 -B scheduler.py check
```

`check` runs once. It matches the current local minute and weekday and records completed sends in `~/Library/Application Support/RoomAutomation/last-runs.json`. Logs go to `~/Library/Logs/room-automation.log`. No late catch-up is performed. Manual controls do not suspend future schedules.

## macOS scheduling

The deployment used a local user LaunchAgent named `com.roomautomation.scheduler` to invoke `scheduler.py check` every minute. A portable installer is not included. A new installation needs a LaunchAgent whose `ProgramArguments` contain the absolute Python executable, absolute scheduler script, and `check`; use `StartInterval` of 60 seconds and writable log paths. Test that configuration on the Mac before relying on it.

For an existing installation, inspect the loaded job:

```sh
launchctl print gui/$(id -u)/com.roomautomation.scheduler
```

An older job, `com.roomautomation.morninglights`, used `lights.py on` at 06:45 Monday–Thursday. The October 10 test record says it was disabled, but this repository cannot establish its current loaded state. Inspect it and the temporary `com.roomautomation.test1030` test job locally. Keep only one scheduling owner; overlapping scheduler processes are not locked against each other.

The Mac must remain awake and the user logged in. A successful send log is not physical confirmation. Verify at least one unattended event by observing the light and recording the result. Sleep/wake, reboot, network failure and repeated-run measurements remain follow-up work.
