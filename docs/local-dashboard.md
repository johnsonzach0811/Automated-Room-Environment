# Local room dashboard

Requires Python 3.9+; no packages, account, or cloud service needed.

```sh
cd Automated-Room-Environment
cp config.json config.local.json  # first setup only; edit device.ip locally
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
backs up the previous file with a .json.bak suffix, and replaces the config atomically.
Reload discards unsaved form edits. Another saved edit causes a stale-revision error;
reload and reapply your changes. Avoid editing the JSON in another program during
saving. Backup files contain local device details; do not commit them.

Schedules use the Mac's local timezone. The dashboard does not run a scheduling
loop or install LaunchAgents. Closing it does not stop an existing scheduler.
All entry points prefer ignored `config.local.json` when present, falling back to
the tracked example `config.json`; `--config` selects a different path.
The tracked example disables every schedule. Enable routines only in your local
configuration after testing the device address and checking existing jobs.
See [scheduler setup and legacy-job migration](configurable-automation.md).

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

## Example schedule

The portable example contains ten disabled, seven-day routines: morning at 07:00,
daytime at 09:00, progressive evening presets every 15 minutes from 18:00 through
19:30, and power off at 23:00. Daytime uses RGB 255/165/85 at 45%; the evening
progression reduces brightness from 40% to 15%. `config.json` is the source of
truth for example values; your ignored local file owns your actual routine.
