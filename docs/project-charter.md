# Project Muse — Phase A Project Charter

Version: 1.0 | Prepared: October 10, 2026 | Status: Initial planning baseline

## Purpose and business case

Muse explores whether existing household technology can complement seasonal decorating through coordinated lighting, visual content, and audio. The intended experience is an atmosphere that changes with time of day and the selected seasonal theme. Customer demand, willingness to pay, and commercial differentiation remain unvalidated hypotheses.

Phase A answers a narrower question: can Zach's existing room devices be coordinated reliably from a Mac-based controller?

## Ownership and authorization

Sponsor, project manager, developer, and acceptance owner: Zachary Johnson.

The sponsor has selected Phase A technical feasibility and authorized project documentation and repository setup. This charter records the initial planning baseline; technical choices and spending commitments remain subject to evidence and explicit decisions. It does not authorize commercial launch or hardware purchases.

## Measurable objective

Within a target of six weeks and 36 total work hours, demonstrate a single interface and schedule coordinating predefined Autumn Morning, Autumn Afternoon, and Autumn Evening scenes. Investigate Govee lighting and Vizio TV control; use Mac audio as a provisional audio endpoint because no external speaker is currently available.

Feasibility requires at least two independently controlled device categories. Mac audio may count as one, but does not establish external speaker compatibility. If TV control fails, explicitly classify the result as conditional feasibility for the original lights-and-TV experience.

## High-level requirements

- Inventory exact models, firmware where available, network requirements, and supported control paths.
- Activate three predefined autumn scenes from one interface.
- Activate lighting scenes according to a user-defined daily schedule.
- Provide a pause/manual override that prevents subsequent scheduled changes until explicitly resumed.
- Make TV and audio activation opt-in; avoid replacing active playback without an explicit user command.
- Report unsupported functions and failures instead of indicating success.
- Keep credentials outside version control.

## Deliverables

| ID | Output | Acceptance evidence |
| --- | --- | --- |
| D1 | Compatibility assessment | Each endpoint has exact identity, evidence, and supported/unsupported/unknown control functions |
| D2 | Controller and integration environment | Reproducible setup instructions and two working categories, with limitations stated |
| D3 | Scene interface | Three autumn presets, activation controls, and automation pause/resume |
| D4 | Scheduled automation | Three scene schedules demonstrated while controller is awake and connected |
| D5 | Verification record | 30 end-to-end executions, including at least 10 scheduled executions; failure and latency records |
| D6 | Feasibility recommendation | Go, conditional go, or no-go with evidence, unresolved risks, and proposed next scope |

## Acceptance and phase gate

Provisional prototype targets: at least 27 of 30 scene executions succeed, and successful executions finish within 10 seconds. An execution succeeds only when all enabled supported actions complete and the resulting state is verified by device feedback or observation. Record retries and partial failures separately. These thresholds are planning choices, not consumer-product reliability claims.

All pause/override tests must pass. Demonstrate that scheduled scenes do not start opted-out TV/audio actions. Include device-offline, controller-restart, and Mac sleep/wake scenarios. Explicitly record whether schedules survive restart and what happens to events missed during sleep; do not silently replay disruptive media actions.

Go: required integrations and acceptance targets pass, with a reproducible setup.

Conditional go: a useful subset works but the original device mix or unattended behavior has blockers; define a revised next phase.

No-go: no viable coordinated experience within the effort ceiling, or critical override/control failures remain unresolved.

## Constraints, budget, and schedule

- Solo project; 5–8 hours available per week.
- Baseline effort: 36 hours, including planning, documentation, and verification.
- Target window: October 10–November 20, 2026. At 5 hours/week, 36 hours takes more than seven weeks; the six-week target assumes roughly 6 hours/week.
- Approved new spending: $0. Use existing equipment and evaluate purchase needs separately.
- Preferred runtime: Mac. Specific controller software remains undecided.
- Known hardware: Vizio TV, Govee LED strips, Mac; exact device models not yet recorded. External speaker: none.
- Mac availability, sleep behavior, network access, and device capabilities constrain unattended operation.

| Milestone | Target | Exit condition |
| --- | --- | --- |
| M1 Compatibility and architecture decision | October 16 | Device evidence, blockers, and a justified architecture decision recorded |
| M2 Integration proof | End of Week 2 | Two categories respond to reproducible commands |
| M3 Scene and schedule demonstration | End of Week 4 | Three presets, schedules, and override demonstrated |
| M4 Phase A decision | November 20 target | Tests, limitations, and recommendation complete |

## Initial effort allocation

| Work area | Hours |
| --- | ---: |
| Planning and M1 assessment | 5 |
| Controller and endpoint integrations | 9 |
| Scene interface, schedule, and override | 10 |
| Verification and corrections | 8 |
| Closure and feasibility recommendation | 4 |
| Total | 36 |

Estimates are provisional. Weekly review compares actual effort, remaining work, and the ceiling; scope or date changes must be recorded.

## Risks and assumptions

| Uncertainty | Response |
| --- | --- |
| Govee strips may lack the needed control path | Confirm exact model before choosing integration software |
| Vizio power/input/media capabilities may be limited | Assess each function independently; avoid assuming network control implies content playback |
| Mac sleep or shutdown prevents schedules | Test availability and missed-event behavior; document operating conditions |
| Media automation interrupts normal use | Opt-in media actions and explicit pause/override |
| Setup complexity exceeds solo capacity | Use existing integration tools where justified; timebox investigation |
| Seasonal aesthetics are liked but not purchased | Defer market validation to a separate phase |
| Brand/app/AI work expands Phase A | Maintain scope exclusions and a future-feature backlog |

## Change control

Record any change to deliverables, acceptance criteria, effort, date, or spending in a decision/change log before implementation. Include reason, alternatives, impact, and sponsor decision. Minor implementation choices within the baseline require a decision record, not a new charter. Close Phase A before committing to the commercial roadmap.
