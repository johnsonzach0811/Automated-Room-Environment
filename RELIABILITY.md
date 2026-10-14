# Connection handling and scheduling

Manual dashboard/CLI presets, scenes, and controls persist a pause before sending.
Invalid input leaves pause unchanged; failed valid manual controls remain paused.
Resume is explicit and never replays missed schedules. Corrupt override state fails
closed as paused. An OS file lock serializes scheduler checks and manual controls;
a pause waits for a running batch and cannot undo commands already sent.

Run history is atomically replaced and flushed while holding the same lock.
A missing history starts empty; unreadable, malformed, or invalid history prevents
scheduled sends and logs an error. Diagnose and back up damaged history before
repairing it. Do not simply delete it during a due minute: that can permit a repeat.
Successful sends are marked per schedule name and local calendar minute. Repeated
checks after a process restart reuse the record. If a batch crosses the minute,
remaining routines are skipped rather than sent late.

Each UDP send has a two-second socket timeout, at most three attempts, one- then
two-second retry delays, and 0.3-second command spacing. Success means local send
acceptance, not device acknowledgement; an offline destination may appear successful.
A failed scene attempts its other targets, reports device failures, and is not marked
complete. A retry within the due minute can resend targets already applied.
Partial presets/scenes can leave partially changed settings. A crash after sending
but before recording history can also permit a repeat: exactly-once physical
execution cannot be guaranteed by this UDP protocol.

Paired identity discovery happens only when a targeted Govee device is controlled.
Missing or ambiguous identity prevents sending to a stale address. An unavailable
unrelated device does not block a scene. Reply port 4002 must be available.
`python3 -B scheduler.py health` performs explicit read-only discovery/status checks;
the dashboard does not continuously report actual hardware state.

Govee transitions apply directly until reliable starting-state feedback is integrated.
Simulated transitions account for elapsed command time with a monotonic clock;
0–30 second durations and 1–60 steps bound each target's transition work. Devices
are processed sequentially. Pause can wait for the active scene to finish.

LaunchAgents require an awake Mac and logged-in GUI session. There is no late
catch-up after pause, sleep, login, or restart. Restart/login and sleep/wake physical
behavior still need observation. The October 12 morning check was paused, not a
verified activation. See docs/verification-2026-10-13.md for the verification matrix.
