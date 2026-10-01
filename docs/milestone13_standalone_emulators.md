# Milestone #13 — Standalone emulators

Status: **COMPLETE AND CLOSED — 2026-10-01.**

The user confirmed the remaining picture, audio and gameplay-controls acceptance
with “Everything Passes”. This human acceptance complements the automated and live
process evidence below. No approved milestone work remains. Milestone #14 has not
started.

## Approved scope and boundaries

The existing architecture gains one opt-in native Linux **Snes9x GTK** SNES adapter.
RetroArch remains the default for every platform. No fallback is attempted when an
explicitly selected standalone backend fails. Other emulator families and operating
systems require separate adapters and qualification.

| Boundary | Owner and behavior |
| --- | --- |
| RVDB knowledge | Existing `RVDBService.platform_view()` supplies canonical SNES ↔ `emulator.snes9x` compatibility. Knowledge is not evidence of local installation. Source/bundle data is unchanged. |
| Local library | Existing scanner, physical edition selection and `local_file_id` remain authoritative. Only loose `.sfc`/`.smc` content is supported by this adapter. |
| User persistence | Existing ConfigLoader/ConfigWriter persist the SNES backend and executable. Existing Library history records the selected physical edition only after startup confirmation. No durable identity/store migration. |
| Presentation | Saved RetroArch overlay, shader and CRT intent is retained. Presentation Studio reports that these controls are not applied by standalone. Library artwork is unchanged. |
| Runtime configuration | `Snes9xLauncher` manages native GTK configuration, save locations and initial keyboard controls. It does not consume RetroArch configs, core options, overlays, shaders or cheats. |
| Execution | `EmulatorSession` exposes the existing ProcessSession protocol and serializes adapter launches. MainWindow, Library, Playlists, polling, Stop and shutdown share this owner. RetroArch's existing launcher remains intact. |

## Files and responsibilities

- `services/emulators/models.py`: canonical routing, executable availability, immutable native launch input and capability text.
- `services/emulators/snes9x.py`: canonical compatibility, file prerequisites, native config/saves, argv execution, ROM-loaded startup evidence and bounded owned-group termination.
- `services/emulators/session.py`: one session coordinator over the existing RetroArch launcher and new native adapter.
- `controllers/game_launch_controller.py`: branch after edition selection and before any RetroArch preparation; shared completion/history handling.
- `config/retroarch.yaml`, `config/validation.py`, `services/settings/service.py`, `ui/pages/settings_page.py`: opt-in settings with independent validation and next-launch activation.
- `services/startup.py`: read-only warnings for a missing selected standalone executable.
- `ui/main_window.py`: shared adapter lifecycle wiring.
- `services/library/presentation_studio.py`, `ui/library/widgets/presentation_studio.py`, `ui/library/details/game_details.py`: accurate native capability reporting without clearing saved preferences.
- `tests/test_standalone_emulators.py`: routing, prerequisites, real process lifecycle, ownership, isolation, settings and UI checks.
- `scripts/qualify_standalone_runtime.py`: isolated real Library discovery, launch/history, Stop, fresh-interpreter relaunch and shutdown.

## Configuration and controls

Settings → **SNES emulator backend** → choose **Snes9x GTK standalone — Linux**, set
the executable, then **Save SNES Backend**. It applies to the next SNES launch;
changing settings does not alter an active process. Switching back to RetroArch
does not delete native saves or presentation preferences.

```json
{
  "emulation": {
    "snes_backend": "snes9x",
    "snes9x_executable": "/absolute/path/to/snes9x-gtk"
  }
}
```

The executable check verifies local availability, not emulation correctness.
Unsupported builds, missing shared libraries, load failures and unconfirmed startup
fail visibly. GTK 1.63 emits `Using rewind buffer of ...` after successful ROM loading;
the adapter enables a 16 MiB rewind buffer and uses that message, with a live owned
process, as startup evidence. An empty GUI alone is insufficient. Other frontend
versions are not automatically qualified.

Configuration is under `$XDG_CONFIG_HOME/retrovault/emulators/snes9x/<identity-hash>/snes9x/snes9x.conf`.
Native saves are under `$XDG_DATA_HOME/retrovault/emulators/snes9x/<identity-hash>/sram`
and `states`. Logs are under `$XDG_CACHE_HOME/retrovault/snes9x/<identity-hash>/session.log`.
Normal XDG home-directory fallbacks apply. The identity hash derives from the
selected physical edition's durable local ID, with absolute ROM path fallback for
direct callers lacking an ID. Same-named physical files do not collide. Existing
native key bindings are retained; owned save/display settings are reapplied at launch.

Initial keyboard controls: arrows for direction, Enter for Start, Tab for Select,
Z/X/A/S for B/A/Y/X, Q/W for L/R. Shift+F1 saves slot 0; F1 loads it;
Alt+Enter toggles fullscreen. Additional gamepad mapping is configured in the native
frontend. RetroArch controller bindings and saves are not imported or synchronized.

## Qualification provenance

Official upstream release: [Snes9x 1.63](https://github.com/snes9xgit/snes9x/releases/tag/1.63).
Downloaded asset: `Snes9x-1.63-x86_64.AppImage`, SHA-256
`21a3d120dac7525a9effac3dbec82bd809dd91684bd46451c010480614427c39`.

The AppImage lacked glibmm on this Ubuntu 26.04 host and its older bundled GTK stack
was incompatible with the host libraries. The unchanged extracted official
`snes9x-gtk` executable (SHA-256
`53908451a53207fad4ba6677c3f1f673b0c23efaa98af53aa1cf7e94b00a2e9a`) is qualified with locally extracted Ubuntu glibmm/gtkmm,
atkmm, pangomm, cairomm and sigc++ runtime packages. Nothing was installed into system
package directories. The local qualification executable is
`build/milestone13/vendor/native/snes9x-gtk`; its original relative RUNPATH finds
matching libraries in `build/milestone13/vendor/lib`. These ignored build artifacts
are qualification prerequisites, not a shipped emulator or automatic installer.

The source contracts were checked against upstream **1.63** `gtk/src/gtk_config.cpp`,
`gtk_s9x.cpp` and `gtk_binding.cpp`. The runner stages a copy of the user's Street
Fighter II Turbo ROM and uses isolated XDG locations. It checks protected original
ROM, RVDB bundle, user JSON files and RetroArch primary config hashes.

The initial live run completed 30 seconds, Stop, fresh-process relaunch and shutdown,
with user files preserved. Its report correctly remained failed because the harness
mistakenly compared GTK `gvfs-metadata` files as game saves. The corrected runner
limits save evidence to native `sram` and `states`. The corrected run in
`build/milestone13/live-snes-verified/report.json` passed **30.037 seconds**, Stop,
a **3.005-second fresh-process relaunch**, shutdown, identity/history persistence
and protected-file preservation. No native save files were produced in these runs.
A game that creates no SRAM is not claimed to validate SRAM contents.

Final automated regression: **2,198 passed** (including **32 new standalone cases**),
recorded in `build/milestone13/automated-tests.log`. Both repositories pass diff
integrity checks. Both RVDB bundles retain the same SHA-256:
`0c32be3117d31830c5c2e4a8554b2c2f627ed7474c81dbc1697511e5afbf3b9a`.
No commit, push, release, user-backend switch or clean-checkout claim is implied.

## Unchanged and outside scope

RVDB data/schema/bundles, RetroArch runtime composition, production package policy,
NES/SNES/Genesis approved bezels/shaders, Library identity, metadata/artwork,
presentation store and hardware-state policy remain unchanged.

No other standalone adapters, Flatpak/Windows/macOS support, game-specific backend
overrides, emulator auto-install/update, native archive handling, firmware workflows,
netplay, cheat integration, save conversion/synchronization or RetroArch visual parity.
Milestone #14 is not started. Live display/audio/input acceptance must come from the
user; process success and mocked tests do not establish it.
