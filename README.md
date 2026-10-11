# Project Muse

Seasonal room atmosphere automation — Phase A technical feasibility.

Status: first lighting integration demonstrated on October 10, 2026. The Mac discovered the Govee H619D over LAN and successfully changed its color and brightness. Tests were run manually in Terminal; this repository does not yet contain a reusable device-control application.

See [the progress record](docs/progress-2026-10-10.md) for evidence and next steps.

## Start here

1. Read [the project charter](docs/project-charter.md).
2. Review [scope boundaries](docs/scope-statement.md).
3. Complete [M1 work packages](docs/m1-work-packages.md), continuing with repeatable lighting tests and the remaining architecture decisions.
4. Record compatibility evidence and the controller decision before implementing integrations.

## Initial hardware

- Vizio TV — exact model unknown.
- Govee H619D LED strips — LAN discovery, RGB color and brightness tested.
- Mac controller — Python 3.14.7 reported by user; macOS version still to confirm.
- External speaker — none; evaluate Mac audio provisionally.

## Tracking

Use GitHub Issues for bounded work packages. Suggested columns for an optional GitHub Projects board: Backlog, Ready, In progress, Blocked, Done. M1 target: October 16, 2026. Phase A target: November 20, 2026, with 36 hours total estimated effort.

Templates live in `templates/`. Phase A success criteria and scope changes are governed by the charter. Basic H619D LAN control is demonstrated on the user's network. Other device compatibility, reliability and market demand remain unvalidated.

## Repository hygiene

Keep API keys, pairing tokens, personal media files, and home network/device details out of commits. Use `.env.example` or redacted configuration if code is introduced. No open-source license has been selected.
