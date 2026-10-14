# Local room dashboard

Requires Python 3.9+; no packages, account, or cloud service needed.

```sh
cd ~/automated-room-environment
python3 -B dashboard.py
```

Open http://127.0.0.1:8765 in a browser on this Mac. Keep the terminal running;
Ctrl-C stops the dashboard. Use `--port 8766` if the port is busy. The server
always binds to 127.0.0.1; there is no public-network bind option. Do not place
it behind a proxy or port forward. Other local users/processes can access it.

Morning and Focus reuse the saved presets. On/off sends only power; brightness
and color send only their respective setting. They do not update presets or
turn a powered-off light on. Manual settings are desired values, not reported
light state. UDP success means commands were sent, not acknowledged. A failed
multi-command preset can leave partially changed settings.

## Schedules

The form loads existing schedules without changing them. Additions start disabled.
Save validates the complete config with validation.py, preserves device and presets,
backs up the previous file as config.json.bak, and replaces the config atomically.
Reload discards unsaved form edits. Another saved edit causes a stale-revision error;
reload and reapply your changes. Avoid editing the JSON in another program during
saving. Backup files contain local device details; do not commit them.

Schedules use the Mac's local timezone and the existing scheduler.py check job.
The dashboard never runs a scheduling loop, installs jobs, edits launchd plists,
or changes the Monday–Thursday 06:45 routine on startup. Closing the dashboard
does not stop launchd. Changes take effect on the next scheduler check.

The local Mac has both com.roomautomation.scheduler and
com.roomautomation.morninglights definitions. The latter directly runs lights.py
on at 06:45 Monday–Thursday; editing this form cannot change that legacy job.
This milestone leaves both jobs untouched. If both are loaded, duplicate commands
are possible. Inspect loaded jobs before changing scheduling ownership; do not
install another scheduler just to use this dashboard. Earlier configurable-automation
notes describe a disabled default; the current config has the morning schedule enabled.

## Verification

```sh
python3 -B -m unittest discover -s tests -v
python3 -B scheduler.py validate
```

Tests use temporary configuration and mocked device commands, including HTTP
security, malformed input, stale saves, backup preservation, and transport errors.
No test changes live config, launchd, or lights. Requests require an exact local
Host, a per-process session token, JSON and a bounded body. Foreign browser origins
are rejected; there is no cross-origin API access. Reload the page after restarting
so it receives a fresh token.

On the Mac LAN, manually try each control and visually check the light, then verify
an unattended scheduled run from logs. These physical checks have not been
performed for this dashboard milestone.

## Daily room schedule (October 14, 2026)

The checked-in `config.json` defines four enabled, seven-day schedules in the Mac's local timezone:

| Time | Preset | Effect |
| --- | --- | --- |
| 07:00 | morning | Warm RGB 255/210/160 at 30% |
| 09:00 | daytime | Neutral warm RGB 255/245/225 at 75% |
| 19:00 | evening | Amber RGB 255/165/95 at 35% |
| 23:00 | night | Power off |

**Mac setup is still required.** Run `git pull`, `python3 -B scheduler.py validate`, and test presets on the Mac. Check `launchctl list | grep com.roomautomation` to confirm the scheduler agent is loaded. The existing legacy `com.roomautomation.morninglights` agent may still fire at 06:45 Monday–Thursday, independently of these schedules. Disable the legacy agent only after verifying its actual loaded state and plist path; do not blindly delete it. Avoid creating a second repeating scheduler. The Mac must remain awake and logged in, with lights reachable on LAN. Inspect `~/Library/Logs/room-automation.log` after the first unattended event to verify the scheduled command was sent; visually confirm the light behavior.
