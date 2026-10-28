# Automated Room Project

A personal engineering project by Zachary Johnson that uses a Mac mini to control room lighting automatically throughout the day.

The goal is to make the room match the time of day without having to adjust the lights by hand. The project currently controls one Govee H619D light strip.

## What it does now

- Turns the lights on and off at selected times.
- Changes brightness and color using saved settings for morning, daytime, evening, and night.
- Supports an evening routine that makes the lighting warmer and dimmer in steps.
- Provides a browser page on the Mac for adjusting the lights and editing schedules.
- Checks settings for mistakes, keeps a record of commands, and retries when the computer reports a sending error.

For example, a daily routine can turn the lights on in the morning, adjust them during the day, dim them through the evening, and turn them off at bedtime. The included example schedules start turned off so they can be reviewed before use.

## How it works

The Mac stores the lighting settings and schedule. Once scheduling is set up, it checks every minute whether a lighting change is due and sends that change to the light over the home network.

The browser controls use the same saved settings. They let you make changes manually, but opening the browser page does not start the automatic schedule. The project is written in Python and does not require extra Python packages.

## What has been tested

| Test | Result |
| --- | --- |
| Changing the actual lights | Manual on/off, color, and brightness tests were recorded on October 10, 2026. |
| Running without a manual command | Two scheduled tests worked on October 10: turning the lights on and switching from the Morning setting to Focus. |
| Checking the program | Automated tests check settings, scheduled changes, repeated checks, error handling, and the browser controls. These tests do not operate the actual lights. |
| Further testing | The browser controls still need a recorded test with the actual lights. Longer daily use and behavior after sleep, restart, or a lost connection also need testing. |

The Mac must stay awake and connected for scheduled changes to run. A change missed while the Mac is asleep is skipped. The program reports when it sends a command, but cannot confirm that the light received it.

Manual adjustments do not pause the schedule: the next scheduled change can replace them.

## Potential future plans

These are possible additions, not features that work today.

- **Pause and resume:** pause automatic changes when adjusting the room manually.
- **Easier setup and more testing:** simplify setup on the Mac and check how consistently the schedule works over time.
- **Seasonal room themes:** change the room's settings based on the time of year.
- **TV and audio:** explore adding background visuals and sound to match the room.
- **Seasonal room scents:** explore automated Amazon deliveries of room scents based on the time of year, so new scents arrive for each season. No ordering or delivery connection has been built or tested.

## Setup

The current setup uses a Mac, Python 3.9 or newer, and a Govee H619D with LAN Control enabled in the Govee app. The Mac and lights must be able to reach each other on the home network.

Download the project and make a separate copy of the example settings for your own room:

```sh
git clone https://github.com/johnsonzach0811/Automated-Room-Environment.git
cd Automated-Room-Environment
cp config.json config.local.json
```

In `config.local.json`, replace `device.ip` with your light's network address. This personal settings file is excluded from GitHub. Review the schedules before turning any on.

Check the settings and open the browser controls:

```sh
python3 -B scheduler.py validate
python3 -B dashboard.py
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765) on the Mac. The buttons send commands to the actual lights.

Automatic scheduling needs a separate Mac background task. See the [schedule setup instructions](docs/configurable-automation.md) and [browser control instructions](docs/local-dashboard.md).

**If the project is already running on your Mac:** before pulling this update, copy your working `config.json` to `config.local.json`. This preserves your light's address and enabled schedules.

To run the program's checks without operating the lights:

```sh
python3 -B -m unittest discover -s tests -v
```

## Project records

- [First successful automatic lighting test](docs/automation-test-success-2026-10-10.md)
- [Successful scheduled lighting change](docs/configurable-scheduler-test-2026-10-10.md)
- [Technical details and limitations](RELIABILITY.md)
- [Original project plan](docs/project-charter.md) and [original scope](docs/scope-statement.md)

The original plans and dated notes show how the project developed. The sections above describe what works now and what is being considered for later.
