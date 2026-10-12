# Local lighting dashboard

Run `python3 -B dashboard.py`, then open http://127.0.0.1:8765 on this Mac. Keep the process running; Ctrl-C stops the dashboard. Use `--port 8766` if needed. It binds only to 127.0.0.1. Do not proxy or forward it to another network. Local users/processes can access it.

Morning and Focus reuse saved presets. On/off sends power only; brightness and color send their setting only and do not turn an off light on. Sliders are desired settings rather than live device state. Success messages report sent commands, not confirmed physical delivery.

Every valid manual control first pauses scheduled lighting. Pause persists after closing the dashboard, restarting a process, or reinstalling the job. Use Resume automation to let subsequent schedules run. Resume does not change the lights immediately or replay missed routines. Pause waits for any current command batch before returning. A failed manual send still leaves automation paused.

Schedule additions start disabled. Save validates the whole config, preserves presets/device, creates `config.json.bak` beside the local config, and atomically replaces it. A stale revision requires reload. Saving schedules never resumes automation. Avoid simultaneous edits from an external editor during saving.

The dashboard never installs or runs a scheduler loop. The existing LaunchAgent reads schedules on each minute check using the Mac's local time. The installer retires the old separate morning job, so dashboard edits control the single intended owner. Existing Monday–Thursday 06:45 config is preserved; a fresh example is disabled.

Requests require an exact local Host; mutations require a per-process token, JSON, and bounded body. Foreign browser origins are rejected. Reload the page after restarting for a new token.

Use the README tests and the dated verification record. The broader scene-engine branch has a separate draft PR and is not part of this deployed dashboard.
