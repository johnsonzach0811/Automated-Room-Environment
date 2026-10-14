# Local dashboard

Run `python3 -B dashboard.py` and open http://127.0.0.1:8765 on this Mac. Keep the
process running; Ctrl-C stops it. Use `--port 8766` if needed. It binds only to
127.0.0.1. Local users/processes can access it.

Preset and individual controls target the configured default device. Named scene
buttons target the devices in each scene. Scene definitions are edited in the private
configuration file. The UI shows desired values rather than current hardware state.
Power, brightness, and RGB controls send only the selected fields on Govee; brightness
and color do not turn an off light on. Scenes apply complete states with documented
defaults. Simulated device state is temporary and resets between requests.

Every valid manual control pauses automation before execution. Pause persists across
process restarts and installer runs. Failed controls still leave automation paused.
Resume permits future routines without changing the light immediately or replaying
missed minutes. Pause waits for an already running command batch.

Schedule targets can be presets or scenes. Additions start disabled. Save validates
the complete config, preserves devices, presets, scenes, and default-device selection,
backs up the original file beside local config, and atomically replaces it. Stale saves
require reload. Saving never resumes automation. Avoid concurrent external editing.

The dashboard does not install a scheduler or run a scheduling loop. The single
installed LaunchAgent reads configuration every minute using the Mac's local time.
Keep the Mac awake and logged in for routines. Closing the dashboard does not stop
the job. Setup uses the preview/apply installer described in installation.md.

Requests require exact local Host; mutations require a session token, JSON, and a
bounded body. Foreign browser origins are rejected. Reload after server restart.
Tests isolate files and LAN commands; physical validation is separately tracked in
the latest verification record.
