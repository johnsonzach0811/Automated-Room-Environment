> Historical record. Current configuration, pause behavior, and installation are described in the README and docs/verification-2026-10-11.md. Earlier pending/disabled statements below describe that moment in development.

# Configurable lighting automation — next milestone

The existing `lights.py` and Monday–Thursday 6:45 AM LaunchAgent are **unchanged**. This feature is staged separately to avoid duplicate morning triggers.

## Try the two presets

```bash
cd ~/automated-room-environment
git pull
python3 scheduler.py preset morning
python3 scheduler.py preset focus
```

Edit `config.json` to change brightness, RGB color, or schedules. Presets are `morning` (warm, 30%) and `focus` (neutral warm, 65%). The IP address is specific to your local network.

## How scheduling will work

`python3 scheduler.py check` examines enabled schedules against the **current local minute and weekday**, executes matching presets, and writes a last-run marker under `~/Library/Application Support/RoomAutomation/` to prevent duplicate runs during the same minute.

The included weekday morning schedule is **disabled by default** so it doesn't overlap the already installed `launchd` morning job. Once presets work, the next step is to install a repeating one-minute LaunchAgent to run `scheduler.py check`, disable the old morning LaunchAgent, and enable the new config schedule. Do **not** enable the new schedule without migrating the old job.

## Limitations

- This is a small scheduler, not a continuously running daemon.
- Running `check` manually only fires a schedule if executed in the matching minute.
- The Mac must be awake and the user logged in for the user LaunchAgent.
- UDP sends do not confirm that lights actually received commands.
- Clock changes, network interruptions and missed minutes may cause skipped triggers; more resilience is future work.
