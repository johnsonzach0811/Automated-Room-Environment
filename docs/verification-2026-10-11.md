# Verification — October 11, 2026

## Installed scheduling audit

At inspection, com.roomautomation.scheduler was loaded in the user's GUI session, configured for all 60 minutes, with 798 executions and last exit code zero. It targeted the Mac's existing checkout. com.roomautomation.morninglights was not loaded; its definition remained on disk. The temporary test1030 definition was absent, and the saved config contained only the enabled Monday–Thursday 06:45 Morning routine. The old Scheduler test run marker was historical, not an active schedule.

The regular 06:45 routine has not yet been observed. The next due run is Monday, October 12, 2026 at 06:45 America/Chicago. Zero exit status between due times does not prove a scheduled physical change.

## Hardware controls

The existing H619D responded to multicast discovery and explicit devStatus queries. Its identity was paired in ignored local configuration. Each dashboard API control was issued through an actual localhost HTTP server and then checked against the physical device's response:

| Control | Verified result | End-to-end elapsed |
| --- | --- | ---: |
| Morning | On, 30%, RGB 255/210/160 | 4.45 s |
| Focus | On, 65%, RGB 255/245/225 | 4.44 s |
| Off | Power off | 3.84 s |
| On | Power on | 3.84 s |
| Brightness | 45% | 3.84 s |
| Color | RGB 255/160/60 | 3.84 s |

Elapsed measurements include identity discovery, command spacing, a 0.5-second settling allowance, and the status read. All returned values matched. Original power, brightness, and color were restored and verified; original automation state was restored. This is device feedback, not a visual aesthetic approval. Only the two full preset executions are scene-like runs; individual controls and restoration are not counted as full Phase A scene executions.

Pause/resume endpoints, browser buttons, and schedule saving passed. All 31 current lighting tests passed. Saving the same schedules preserved the existing routine. Manual changes left automation paused; Resume cleared it. Automated tests additionally cover persistence across processes, corrupted-state fail-closed behavior, failed manual sends, no replay of missed minutes, and mutual exclusion with scheduled changes.

## Recovered scenes branch

Downloaded and verified the complete Git bundle from the prior conversation. Its original five commits were imported and pushed as feature/modular-scenes; tip 1de4ccca2c5853131ebbeaff2b17d6c0c7566da0. It descends directly from main c8d7a435eeb2825499bc8d0b0fd20356d236fa31. All 63 recovered tests passed independently.

Draft PR #1 preserves that work for review. It is not deployed. Review found default-device synthesis/routing issues in devices-only configs, dashboard loss of scene schedule targets, unbounded/non-finite transition parameters, and fades based on default/requested state with send delays added to nominal duration. These should be corrected before merge. Simulated device tests do not establish multi-device physical compatibility.

## Deployment

Installed feature/lighting-controls on the existing Mac checkout. Prior uncommitted dashboard/reliability files were preserved in a named Git stash and a separate file backup. The installer backed up local configuration and previous LaunchAgents, retired the unloaded legacy definition, and loaded a single scheduler. The enabled Monday–Thursday 06:45 routine and presets were preserved. The installed job subsequently completed two unattended minute checks with exit code zero; neither was a due lighting run. Automation is resumed. The updated dashboard is running at http://127.0.0.1:8765. PR #2 contains this update; main is unchanged pending review.

A one-time follow-up is scheduled for Monday October 12 at 06:50 America/Chicago to inspect the regular 06:45 result. It will not send lighting commands or override a user pause.

## Scope boundary

This work does not complete M1 or Phase A. TV/audio and original-versus-lighting-only scope will be decided with the user separately. The normal Monday run, restart/login, sleep/wake, and physical offline scenarios remain pending. Historical records remain intact with current-status notices.
