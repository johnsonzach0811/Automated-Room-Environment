# Project Muse

Seasonal room atmosphere automation — Phase A technical feasibility.

Status: planning. This repository contains project documentation and tracking templates; it does not yet contain a device-control application.

## Start here

1. Read [the project charter](docs/project-charter.md).
2. Review [scope boundaries](docs/scope-statement.md).
3. Complete [M1 work packages](docs/m1-work-packages.md), beginning with exact TV and Govee model numbers.
4. Record compatibility evidence and the controller decision before implementing integrations.

## Initial hardware

- Vizio TV — exact model unknown.
- Govee LED strips — exact model unknown.
- Mac controller — runtime details to confirm.
- External speaker — none; evaluate Mac audio provisionally.

## Tracking

Use GitHub Issues for bounded work packages. Suggested columns for an optional GitHub Projects board: Backlog, Ready, In progress, Blocked, Done. M1 target: October 16, 2026. Phase A target: November 20, 2026, with 36 hours total estimated effort.

Templates live in `templates/`. Phase A success criteria and scope changes are governed by the charter. Compatibility and market demand are not established yet.

## Repository hygiene

Keep API keys, pairing tokens, personal media files, and home network/device details out of commits. Use `.env.example` or redacted configuration if code is introduced. No open-source license has been selected.
