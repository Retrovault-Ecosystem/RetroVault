# USQE Milestone #6 — controller profiles

Status: **complete and closed following user approval of the final report.**
Closure is recorded in the working tree; not committed or published.
The user approved the bounded controller foundation with keyboard/mouse available
and physical gamepads deferred until hardware is available. Milestone #7 is unstarted.

## Implemented behavior

- Existing emulator controls remain the default when no controller preferences exist.
- Settings offers separate RetroArch/native Snes9x profiles, up to two players,
  keyboard on Player 1, explicit device selection and twelve standard gameplay bindings.
- Preview validates a draft and current assignments without saving or affecting games.
  Apply uses the existing atomic settings writer. Cancel restores the saved draft;
  Reset prepares existing-controls mode and requires Apply to persist it.
- Saved intent contains device identity, not a persistent enumeration index. GUID plus
  serial can resolve a reconnected device; absent serial requires the same discovery
  session and instance. Ambiguous matches, disconnected devices and duplicate player
  assignments fail before launch rather than silently choosing another device.
- Refresh retains assignments and edits. Keyboard-only operation does not require SDL2.
  Optional SDL2 discovery closes opened joystick handles and reports unavailable discovery.
- Managed RetroArch controls modify only its owned transient primary config. Managed
  mode disables automatic controller/remap fallback, clears unused bindings and uses
  explicit player ports. Existing mode emits no controller overrides.
- Managed native Snes9x controls use an owned temporary XDG configuration copy. The
  permanent native profile is read, not rewritten. Native save directories retain their
  existing physical-edition ownership. Alternate/turbo/sticky bindings are cleared in
  the temporary copy; explicit conflicting keyboard shortcuts reject launch.
- Temporary native controls are removed after Stop or failed process creation/write.
  Existing process/group ownership remains responsible for stopping emulator processes.

## Component boundaries

`config/controller_preferences.py` validates saved intent; `config/validation.py`
and `services/settings/service.py` reuse existing persistence. `services/input/`
owns discovery, assignment resolution, backend translation and isolated RetroArch
text composition. `ui/widgets/controller_settings.py` owns drafts and feedback;
`ui/pages/settings_page.py` hosts it. The existing launch controller, standalone
request, RetroArch primary runtime/launcher and Snes9x adapter apply these profiles.

RVDB knowledge, library identity, readiness/core policy, presentation resolution,
save policy and lifecycle ownership remain their existing authorities. Controller
preferences are local application settings, not RVDB records or presentation state.

## Qualification and limits

Automated results and user-observed acceptance are separate. Final regression on
2026-10-14: **2,357 passed**, using isolated configuration/data/cache directories.
Evidence: `build/usqe6/enter-fix-verification/full-suite.log` (local ignored evidence).
Affected checks passed at intermediate checkpoints (193 integration checks and
156 controller/runtime/pipeline checks); the final full suite includes all changes.
A read-only installed-config check found that `input_driver = "x"` was being mistaken
for an X-key shortcut; that guard was corrected and has a regression. Changed Python
files parse, and Git whitespace checks pass.

Live automated evidence, 2026-10-14:

| Route | Observed duration | Automated result |
| --- | --- | --- |
| NES RetroArch | 30.033 seconds | Pipeline, actual managed directives, Stop, cleanup and protected-file preservation passed |
| SNES RetroArch | 30.032 seconds | Same checks passed |
| Genesis RetroArch | 30.030 seconds | Same checks passed |
| Native Snes9x | 30.038 seconds, then 3.004-second fresh-process relaunch | Both runs passed; actual managed directives verified; temporary controls removed; user state preserved |

Reports: `build/usqe6/{nes,snes,genesis,native}-keyboard-20261014/report.json`.
These process/configuration results **do not establish working gameplay input**.
The user reported partial controls during initial qualification. Investigation found
that shared `return` preferences must translate to RetroArch's `enter` spelling;
native Snes9x continues to use `Keyboard Return`. The correction passed 143 focused
checks, including two new regression cases. The corrected NES run passed automated
checks over 30.031 seconds (`build/usqe6/nes-enter-fixed-20261014/report.json`).
The user subsequently confirmed: "All NES controls worked" for Enter, arrows, X and Z.
Earlier NES runs remained alive until the runner's deadline; those reports do not
support an Enter-triggered crash. All four keyboard routes now have user acceptance.

The corrected SNES repeat passed automated checks over 30.033 seconds, including
managed directives, protected-file preservation and transient cleanup. Report:
`build/usqe6/snes-enter-fixed-desktop-20261014/report.json`. The initial sandboxed
attempt could not allocate a Flatpak instance; the desktop retry succeeded.
The user confirmed: "All SNES controls worked" for Enter, arrows, X/Z/S/A and Q/W.

The corrected Genesis repeat passed automated checks over 30.031 seconds, including
managed directives, protected-file preservation and transient cleanup. Report:
`build/usqe6/genesis-enter-fixed-desktop-20261014/report.json`.
The user confirmed: "All Genesis controls worked" for Enter, arrows and A/Z/X.

The native Snes9x repeat passed a 30.040-second run and 3.004-second fresh-process
relaunch. Both verified managed directives, Stop and temporary-controls cleanup;
protected user state was preserved. Report:
`build/usqe6/native-keyboard-repeat-desktop-20261014/report.json`.
The user confirmed: "All native snes9x controls worked" for Enter, arrows,
X/Z/S/A and Q/W. This completes the approved keyboard acceptance matrix.

RVDB remains unchanged. Canonical and installed bundles have equal SHA-256:
`4d99f2b1bff694f26ca1b1ff68b7d4d1816236abb1e64d10a62e14bf20e3eb43`.

The isolated qualification runners accept `--managed-keyboard`; RetroArch requires
`--pipeline`. They write only isolated preferences, verify the actual generated
controller directives, preserve protected production files and retain cleanup evidence.
Native qualification verifies a fresh-process relaunch and temporary controls removal.

Deferred hardware evidence and scope limits:

- Physical gamepad model/transport selection, actual button numbering, two-player
  behavior, identical-device ambiguity, disconnect/reconnect and backend enumeration
  equivalence (including host SDL2 versus Flatpak SDL2). These are not qualified.
- USB/Bluetooth/Wi-Fi describe connections, not a support guarantee. Transport pairing,
  drivers and emulator device availability remain prerequisites.
- This slice supports keyboard keys, numbered buttons and signed axes. Raw hat mappings,
  specialized peripherals, extra players and auxiliary controller buttons are not covered.
- Profiles are applied at launch. No live rebinding, automatic pause or guaranteed
  backend hotplug behavior is claimed. Refresh/Preview report current discovery state.

Native Snes9x and RetroArch use different input namespaces; their profiles cannot be
assumed interchangeable. Source checks used the qualified versions' upstream
[RetroArch SDL2 driver](https://github.com/libretro/RetroArch/blob/v1.22.2/input/drivers_joypad/sdl_joypad.c)
and [Snes9x GTK bindings](https://github.com/snes9xgit/snes9x/blob/1.63/gtk/src/gtk_binding.cpp).

## Protected surfaces and closure

The approved bounded implementation and keyboard qualification are complete.
All 2,357 automated tests passed; the user accepted NES, SNES and Genesis through
RetroArch and SNES through native Snes9x. Live reports verify lifecycle cleanup and
protected-file preservation. Physical gamepad qualification remains deferred by
the approved scope and is not a claim of tested hardware support.

No RVDB source/schema/ID changes, core/readiness changes, production artwork, shaders,
logos, calibrated geometry or gameplay package changes. Real user controller settings
are not applied by the qualification runners. Existing original-roadmap historical
records remain unchanged. The user approved finalization after accepting all four
keyboard routes and reviewing the final implementation report. All approved bounded
Milestone #6 work is complete. Physical-device qualification remains explicitly
deferred; it is not promoted into a support claim. Milestone #7 remains unstarted.
No export audit, commit or push was performed as part of this closure record.

## Requested repeat checks — 2026-10-15

The user requested additional corrected SNES and Genesis runs. The SNES run passed
its automated pipeline, managed-key directives, Stop, cleanup and protected-file
checks; the user confirmed "SNES passes" and "All SNES controls worked".
Report: `build/usqe6/snes-enter-fixed-20261015/report.json`.

The Genesis repeat also passed its automated pipeline, Stop, cleanup and protected-file
checks. Report: `build/usqe6/genesis-enter-fixed-20261015/report.json`.
The user confirmed "All Genesis controls worked". Both requested repeats are
accepted, completing the additional checks. Earlier accepted qualification and
closure records remain preserved. No production code changed for these repeats,
and no commit or push was performed. USQE Milestone #6 remains complete within
its approved bounded scope; Milestone #7 remains unstarted.
