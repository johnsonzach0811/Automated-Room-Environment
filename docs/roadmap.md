# Roadmap: Automated Room Environment → Muse MVP

**Vision:** Muse is a home atmosphere automation platform. Users control
lighting, televisions, speakers, and other connected devices through
schedules, presets, and natural-language commands.

**Where we are (2026-10-11):** the modular foundation is in place —
`devices/` abstraction (Govee LAN + simulated), a scene engine with
transitions, config-driven presets/schedules, macOS launchd one-shot
checks, a loopback dashboard, and 63 automated tests. Standard library
only; no cloud accounts, keys, or paid services.

Conventions for this roadmap: work stays local-first and free-tier.
Anything marked **[HW]** needs physical hardware to verify — document
results in `docs/` and continue with other tasks.

## Phase 1 — More devices (next)

- [ ] **Govee LAN discovery.** Replace hardcoded IPs with UDP discovery
  broadcasts so new strips join without config edits. [HW]
- [ ] **Vizio TV integration.** Identify the exact model, then evaluate
  control paths (SmartCast local API / IR blaster / HDMI-CEC via Mac).
  Add a `VizioTV` device subclass behind the existing `Device` ABC. [HW]
- [ ] **Speaker output.** Per the charter, evaluate Mac audio provisionally
  (system volume / playback control); add a `Speaker` device type when a
  protocol is chosen. [HW]
- [ ] **Per-device health checks.** Periodic lightweight polling where the
  protocol allows it; surface unreachable devices in the dashboard instead
  of failing silently on UDP fire-and-forget.

## Phase 2 — Robustness and daily use

- [ ] **State reconciliation.** On schedule runs, compare desired vs.
  last-known state and only send deltas; reduces LAN chatter and partial
  states.
- [ ] **Dashboard scenes UI.** Add scene creation/editing to the local
  dashboard (currently presets + schedules only).
- [ ] **Multi-room support.** Namespace devices and scenes by room in
  config; dashboard groups controls per room.
- [ ] **Notifications.** Optional local notifications (macOS) on schedule
  failures; no external services.
- [ ] **Backup/restore.** Versioned config snapshots before dashboard
  edits (the `.bak` mechanism already exists — surface it in the UI).

## Phase 3 — Natural language

- [ ] **Local command parser.** Map typed commands ("movie night",
  "lights off in 20 minutes") to scenes/schedules without cloud APIs.
  Start with keyword + fuzzy matching; no LLM dependency required.
- [ ] **Scene suggestions.** Propose scenes from usage history
  (e.g. "you run focus at 9 AM weekdays — save it as a scene?").
- [ ] **Voice (deferred).** Only after typed commands are solid; evaluate
  macOS dictation/Siri Shortcuts as input, never as a dependency.

## Phase 4 — Packaging

- [ ] **One-command setup.** Script that installs the launchd job,
  validates config, and runs a simulated smoke test.
- [ ] **License selection.** No open-source license chosen yet — decide
  before any public release.
- [ ] **Mobile-friendly dashboard.** Responsive layout for the existing
  loopback UI; still local-only, no accounts.

## Explicit non-goals (for now)

- Cloud accounts, remote access, or multi-user support.
- Paid APIs or services.
- Voice assistants as a primary interface.
- Non-Govee lighting protocols until the Govee path is boring.

## Decisions log

| Date | Decision |
|------|----------|
| 2026-10-11 | Modular `devices/` ABC; Govee LAN + simulated types; scenes with transitions; launchd one-shot model kept. Standard library only. |
| 2026-10-10 | Govee H619D LAN control demonstrated; launchd weekday-morning schedule live. |

## Milestones

- **M1** (2026-10-16): remaining work packages in `docs/m1-work-packages.md`.
- **Phase A** (2026-11-20): 36h estimated total; success criteria in the
  project charter.
- **Muse MVP**: Phases 1–2 complete + typed natural-language commands
  (Phase 3 core). Revisit date after M1.
