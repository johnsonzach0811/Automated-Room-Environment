# Connection handling and automated tests

Run `python3 -B -m unittest discover -s tests -v` from the repository.
Tests use fake sockets and temporary schedule state; they never send LAN commands
or modify launchd jobs, live logs, configuration, or production run history.

Both scheduler.py and the legacy lights.py use transport.py. Each UDP send has a
2-second socket timeout, at most three attempts, and 1- then 2-second retry delays.
Errors identify the command and destination. Socket initialization errors and
exhausted sends exit with status 1. Successful sends retain the original 0.3-second
spacing. Success means the operating system accepted a datagram, not that the
light received or applied it; an offline UDP destination may produce no error.

A failed scheduled preset is not marked complete; remaining due schedules are
still attempted. Launchd may retry within the same scheduled minute, but there is
no late catch-up. A partially applied preset may leave some light settings changed.

The existing Monday–Thursday 06:45 configuration and launchd files are preserved.
Two launchd definitions exist locally (scheduler and legacy morninglights).
Their loaded status was not available from the initial restricted session;
if both are loaded, both can send commands at 06:45. Neither is changed here.

Validation also rejects non-string preset references with ConfigError rather than
an unexpected TypeError. No dependencies are needed beyond Python's standard library.
