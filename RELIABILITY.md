# Connection handling and scheduling

Run `python3 -B -m unittest discover -s tests -v`. Tests isolate configuration, override state, run history, and sockets; they never send LAN controls or edit LaunchAgents.

Each UDP send has a two-second socket timeout, at most three attempts, and one- then two-second retry delays. Success retains 0.3-second spacing and means local send acceptance, not device acknowledgement. Partial presets may leave partially changed settings. Failed schedules are not marked complete; other due schedules continue. Retry is possible within the same minute; no late catch-up occurs.

Manual dashboard/CLI controls persist a pause before sending. A failed valid manual command also pauses. Invalid input does not alter pause state. Resume is explicit and does not replay missed routines. An OS file lock serializes manual controls, pause changes, and scheduler checks across processes. A pause cannot undo commands already in progress; once it returns, later scheduled changes are blocked. Corrupt override state defaults to paused.

Paired device identity enables bounded discovery before each control batch; an unavailable/ambiguous device prevents a send. Status reads are explicit verification tools, not continuously polled dashboard state.

On October 11 the configurable scheduler was loaded with zero last exit status, and the legacy morning job was not loaded. Temporary test jobs and schedule entries were absent. Installation cleanup now retires legacy definitions with backups. See the dated verification record for hardware evidence and the pending regular Monday 06:45 run.
