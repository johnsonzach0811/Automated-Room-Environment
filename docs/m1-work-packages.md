# M1 — Compatibility and Architecture Decision

Target: October 16, 2026 | Effort allowance: 5 hours total | Owner: Zachary Johnson

Milestone is a zero-duration decision point. The work packages below produce its evidence. This is an initial WBS slice, not the full project WBS.

| WBS | Work package and output | Hours | Predecessor | Done when |
| --- | --- | ---: | --- | --- |
| 1.1.1 | Establish charter/scope and requirements checklist | 0.75 | None | Baseline reviewed and open decisions listed |
| 1.1.2 | Inventory devices and runtime | 0.5 | 1.1.1 | Exact models, Mac OS, connectivity and availability recorded locally |
| 1.1.3 | Assess Govee control capabilities | 1.0 | 1.1.2 | Model-specific sources and one candidate path or blocker recorded |
| 1.1.4 | Assess Vizio functions individually | 1.0 | 1.1.2 | Power, input, status and ambient playback classified with evidence |
| 1.1.5 | Assess Mac audio and controller options | 0.75 | 1.1.2 | Audio path and controller installation/availability constraints documented |
| 1.1.6 | Select architecture and close M1 | 1.0 | 1.1.3–1.1.5 | Decision, fallback, effort implications and Week 2 integration tasks recorded |
| | Total | 5.0 | | |

Packages 1.1.3–1.1.5 have no mutual dependency but share one person; they are sequenced within the weekly capacity. Count documentation effort already spent toward the allowance.

## Assessment record

For each endpoint record model, source link/date, control transport, local/cloud dependency, authentication, supported functions, power-on limitations, test status, and unresolved questions. Keep sensitive identifiers in a local ignored file. A source-supported path is a candidate, not a tested integration.

## Architecture decision criteria

Compare an existing automation controller running on the Mac against a small custom service using model-supported interfaces. Score setup effort, endpoint support, schedule reliability, override support, local/cloud dependency, maintenance burden, and available learning time. Choose the simplest option that supports the verified device mix. Do not choose an app or Bluetooth stack before this assessment.

Proposed logical structure, pending M1: scene controls → scene/schedule coordinator → model-specific adapters → lighting, TV and Mac audio. The coordinator owns opt-in media rules and pause state.

## Exit checklist

- [ ] Exact TV and light-strip models identified.
- [ ] Each requested function classified as supported candidate, tested, unsupported, or unknown.
- [ ] Controller selected with rationale and a fallback.
- [ ] Mac sleep, restart and network assumptions recorded.
- [ ] Two-category demonstration path identified, or scope reduction proposed.
- [ ] Next week's tasks estimated within available hours.

If a blocker remains unknown at the timebox, close M1 as conditional with a bounded follow-up task. Do not label compatibility validated without evidence.
