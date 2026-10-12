> Historical record. Current configuration, pause behavior, and installation are described in the README and docs/verification-2026-10-11.md. Earlier pending/disabled statements below describe that moment in development.

# Configurable scheduler: unattended test successful

On October 10, 2026, user confirmed that the Mac mini's new `com.roomautomation.scheduler` LaunchAgent automatically ran `scheduler.py check`, read a temporary `Scheduler test` entry from local `config.json`, and switched the Govee H619D lights from the Morning preset to the Focus preset at **10:39 PM local time**.

This validates config-driven scheduling and preset switching without manual intervention.

## Current architecture

- `config.json`: device, preset and schedule definitions
- `scheduler.py`: applies presets and checks due schedules
- `launchd`: invokes scheduler every minute
- Govee H619D: receives LAN UDP commands

## Cleanup and follow-up

- Remove the temporary `Scheduler test` entry from the Mac's `config.json` to avoid weekly repeats (user instructed; not independently confirmed).
- The original `com.roomautomation.morninglights` job was disabled locally and `Weekday morning` enabled in the new config per user confirmation.
- Verify regular Monday–Thursday 06:45 execution.
- Add validation, logging, recovery from transient LAN failures, and an easy way to edit schedules.

Note: This commit documents the result; the user's locally edited `config.json` has not been pushed to GitHub. The repository default still has `Weekday morning` disabled until local changes are committed.
