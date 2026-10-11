# Installation and recovery

Use the README setup from a stable checkout on the Mac. Enable LAN Control on the device. Keep `local/config.json`, configuration backups, and paired identity private.

`python3 -B scripts/install_launchd.py` previews a LaunchAgent using the actual checkout and Python executable paths. `--apply` validates configuration first, backs up existing jobs/config under `local/installation-backup-*`, copies legacy config to `local/config.json`, unloads the legacy morning/test1030 jobs if loaded, and loads one configurable scheduler. The calendar trigger covers every minute. It does not enable disabled example schedules or run a preset during installation.

The user LaunchAgent requires a logged-in GUI session and an awake Mac. After updating Python or moving the checkout, rerun the installer with the intended `--python` and `--repo` paths. Restart/login and sleep/wake hardware behavior still require observation. Missed minutes are skipped.

## Device address changes

Run `python3 -B scripts/discover_light.py` and select the exact device identity of your H619D. Pair it once using `--update --device-id YOUR_DEVICE_ID`. This backs up and updates only the ignored local configuration. Thereafter controls discover that identity before each command batch, so a DHCP address change does not require code edits. Discovery takes up to three seconds. If the paired device is missing or ambiguous, controls fail rather than send to a stale address. Multicast requires LAN access and LAN Control enabled; other tools must not occupy UDP reply port 4002.

A router DHCP reservation is optional; it is not configured by these scripts. Discovery and device-status queries follow [Govee's official LAN guide](https://app-h5.govee.com/user-manual/wlan-guide).

## Inspect the installed owner

```sh
launchctl print gui/$(id -u)/com.roomautomation.scheduler
launchctl print gui/$(id -u)/com.roomautomation.morninglights
python3 -B scheduler.py status
tail -n 30 ~/Library/Logs/room-automation.log
```

The scheduler should be loaded; the legacy job should be absent. `state = not running` is normal between one-minute checks. A zero exit code confirms the check completed, not a physical lighting change. Verify due runs with the schedule log, last-runs marker, and device status or room observation.

## Recovery

Stop the configurable job with `launchctl bootout gui/$(id -u)/com.roomautomation.scheduler` before restoring a backed-up installation. Restore the prior code/config and scheduler plist from the installation backup, then bootstrap that single job. Do not load both the legacy morning and configurable scheduler for the same routine. Backups also preserve the retired legacy definition if explicitly needed later.

Pause is stored separately at `~/Library/Application Support/RoomAutomation/automation.json`. It survives code updates and job reinstalls. Use explicit Resume to clear it. A malformed/unreadable override file fails closed as paused. Concurrent manual and scheduled controls share `control.lock`; a pause can wait for a command already in progress.
