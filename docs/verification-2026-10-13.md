# Scene integration and daily reliability — October 13, 2026

This change combines feature/lighting-controls and feature/modular-scenes in an
isolated checkout. The installed Mac checkout, LaunchAgents, private configuration,
light state, and pause state were not changed by this development work.

## Implemented

- Named device/scene controls retain persistent override and shared process locking.
- Validation does not synthesize a network device from a simulated-only config.
- Presets/default controls route explicitly; conflicting default definitions fail.
- Dashboard schedule editing preserves preset or scene targets and all definitions.
- Paired identities resolve for targeted hardware; unrelated devices do not block scenes.
- Govee fades apply directly until real starting-state feedback is integrated.
- Transition parameters are finite and bounded; simulated timing includes command time.
- History writes are atomic; corrupt history blocks scheduled sends.
- Restart deduplication and skipped/paused minute behavior have isolated tests.
- A read-only `health` CLI reports hardware replies without resuming or sending controls.

## Automated verification

All 83 standard-library tests pass, including real localhost HTTP requests with
mocked LAN sends. Added regression coverage checks device routing, scene API
errors and pause behavior, schedule target preservation, transition bounds/timing,
corrupt history, atomic replacement failure, and restart/skipped-minute behavior.
Installer tests operate on temporary homes with mocked launchctl. A browser
check using simulated devices and temporary config verified scene buttons,
persisted pause feedback, and scene-target preservation after saving schedules.

## Physical verification still required

| Check | Evidence required | Status |
| --- | --- | --- |
| Ordinary 06:45 routine | Explicitly resume beforehand; log due event, history marker, and matching light feedback/observation | Pending; October 12 was skipped while paused |
| Manual override | Scene/manual action pauses; next due routine skips; explicit Resume allows a later routine | Previous branch hardware evidence; integrated scene path pending |
| Restart/login | One scheduler owner loads with correct paths; pause persists; future due routine works | Pending |
| Sleep/wake | Missed minute is skipped; next future routine works while awake | Pending |
| Device offline | Failure/status unavailability is visible; pause is retained; next future run after recovery is checked | Pending |
| DHCP address change | Identity resolves to the same physical light; unavailable identity sends nothing | Existing discovery logic tested; physical recovery pending |
| Scene execution | Target colors/power match on H619D; partial failures reported | Integrated path pending |

Do not infer physical success from a zero exit status between due minutes, a mock
or simulated result, or a sent-command history marker alone. Current hardware
state cannot prove a historical paused run happened. Preserve logs and timestamps
for each observation. Follow installation.md and RELIABILITY.md for recovery.

M1 and Phase A remain open. TV/audio compatibility and the original scope gate are
unchanged. No future automation, resume action, or installation was scheduled here.
