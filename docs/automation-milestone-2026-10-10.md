# Automation milestone — October 10, 2026

## Confirmed working
- Govee H619D LAN control enabled.
- Device discovered on LAN at `192.168.4.29` (local DHCP address; may change).
- `lights.py on` and `lights.py off` successfully control the real lights.
- macOS `launchd` job `com.roomautomation.morninglights` installed locally for Monday–Thursday at 06:45.
- Manual `launchctl kickstart -k gui/$(id -u)/com.roomautomation.morninglights` successfully triggered the lights after an earlier transient `OSError: [Errno 65] No route to host`.
- Mac mini has automatic system sleep disabled; Python local-network permission enabled.

## Pending verification
- A separate 22:30 local-time calendar-trigger test was prepared for October 10. **Not yet confirmed to have fired automatically.** The test plist is local to the Mac and should be removed afterward.
- The 06:45 recurring trigger has not yet been observed firing unattended.

## Architecture
`launchd` (Mac mini) -> Python `lights.py` -> Govee LAN UDP port 4003 -> H619D.

## Local setup (existing Mac)
The scheduled plist is stored at:
`~/Library/LaunchAgents/com.roomautomation.morninglights.plist`

It runs `python3 lights.py on` with an absolute Python path at 06:45 on weekdays 1,2,3,4 (Mon–Thu). The schedule is not yet version-controlled. To inspect:
```bash
launchctl print gui/$(id -u)/com.roomautomation.morninglights
cat ~/Library/Logs/room-lights-error.log
cat ~/Library/Logs/room-lights.log
```

## Next engineering steps
1. Verify an unattended calendar trigger.
2. Preserve a portable `launchd` installation script or template in GitHub, with dynamic home and Python paths.
3. Add retries and useful error logging for transient network failures.
4. Add basic configurable presets and eventually a simple interface.
5. Consider DHCP reservation / rediscovery instead of a hard-coded IP.

## Important limitation
GitHub stores code and documentation, but does not run local-network lighting schedules. `launchd` runs on the Mac; any schedule changes must be installed there.
