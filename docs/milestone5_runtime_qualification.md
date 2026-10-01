# Milestone #5 — Finish & qualify RetroArch runtime

Current audit status: **COMPLETE — re-closed with user visual confirmation, 2026-09-29.**
The user confirmed that everything runs exactly as intended after the Genesis
Library metadata correction and explicitly authorized reclosure. Earlier audit
and pending statements below describe historical checkpoints, not outstanding work.

Status (2026-09-29): **COMPLETE for the approved Milestone #5 scope.** Runtime implementation and automated checks pass. The Genesis inversion/placement defect is corrected and user-confirmed; the user also explicitly accepted NES/SNES presentation and startup transitions for all three observed systems.

## Existing architecture retained

RVDB supplies knowledge, not installed-core or runtime state. Local library identity, user favorites/recent persistence, platform presentation selection, transient runtime composition, and emulator execution keep their existing owners. No RVDB data, core mappings, package readiness declarations, durable library identity, or persistent presentation preferences were changed for this milestone. NES/SNES/Genesis remain the existing READY platforms; this work promotes no additional platform.

## Implemented runtime changes

- `RetroArchLauncher` retains the process-group ID captured at spawn, including when a wrapper exits before its descendants. A surviving group blocks another launch and prevents transient cleanup. Stop drains that exact group with bounded TERM/KILL escalation; a failed drain retains ownership for retry.
- `process_group.py` shares the bounded termination mechanism with the content-loaded geometry probe. Probe resources remain owned until drain succeeds, and reentry is refused while its process remains live.
- `ProcessLifecycleAdapter.poll()` recognizes synchronous Stop completion after the launcher clears its handle. Immediate startup exit cannot produce a Running/recent success in the game-details flow.
- Main-window close and Qt Quit attempt shutdown; failure keeps the window/quit event open and reports the error. `aboutToQuit` is an idempotent fallback. The lifecycle timer stops after successful shutdown.
- Runtime file writers register ownership before writing. Primary configs and cheat roots now have explicit tracked cleanup. Cleanup attempts all independent resource owners and retains failures for retry. The archive extraction cache remains outside one-launch cleanup.
- `scripts/qualify_retroarch_runtime.py` executes a single 1–30 second production launch with isolated save/state/output paths. It records source/core hashes, command, duration, Stop/shutdown results, remaining ownership and transient files. A shared file lock prevents simultaneous runner invocations; failed process drain leaves a blocking marker for investigation. The logging wrapper executes the configured executable, adding verbose/log-file arguments only. Visual acceptance is never inferred by the script.

## Evidence

Final full automated suite after the Genesis projection correction: **1,942 passed**. The focused lifecycle/failure-path suite: **31 passed**. Tests use `QT_QPA_PLATFORM=offscreen` and an isolated `XDG_CACHE_HOME`; GUI tests do not establish live visual acceptance.

Actual host: Wayland, configured `/usr/bin/retroarch` wrapper, Flatpak RetroArch 1.22.2. Initial sandbox attempt failed with `Unable to allocate instance id`; the authorized runs outside that sandbox succeeded. Each live run completed before the next started.

| Platform / fixture | Runtime observation | Stop / shutdown | Transients / owned group |
| --- | --- | --- | --- |
| NES / Duck Tales 2 (U) | Alive through 10.010 seconds | Passed | None remaining |
| SNES / Street Fighter II Turbo (USA) (Rev 1) | Alive through 10.010 seconds | Passed | None remaining |
| Genesis / Sonic The Hedgehog (USA, Europe) | Alive through 10.011 seconds | Passed | None remaining |

Local evidence (ignored build artifacts):

- `build/milestone5/nes-04/report.json` and `retroarch.log`
- `build/milestone5/snes-01/report.json` and `retroarch.log`
- `build/milestone5/genesis-01/report.json` and `retroarch.log`

User-requested repeat: NES (`nes-05`), SNES (`snes-02`), and Genesis (`genesis-02`) each remained alive for the full 20-second observation, then passed Stop/shutdown with no owned group or transient files remaining. Source configuration hashes again matched. The user subsequently accepted NES/SNES presentation and all three startup transitions; Genesis required the projection correction recorded below.

The persistent primary configuration SHA-256 remained `df6aff21b9193f3a1e90420ce0255be14e4bf8255fdfb0e7fc96f96b9dfd064d` across every live run. Logs show GLCore/video, core and shader initialization; these are process/initialization observations, not proof of correct pixels, input, sound, long-session stability, or save round trips. Stop uses process-group termination; the test does not establish graceful in-emulator save completion.

## Acceptance and closure

The user confirmed the corrected Genesis image is upright and correctly positioned inside the bezel, then confirmed NES/SNES presentation and startup transitions for all three observed systems were acceptable. This closes the previously pending launch-transition acceptance for these fixtures in `a4c8_viewport_qualification.md`.

No required work remains in the approved milestone scope. These are bounded host/fixture qualifications, not a claim of all-game compatibility, long-session stability, input/audio certification or save round-trip testing. The existing architecture and platform readiness declarations remain intact. Milestone #6 has not started.

## Scope limits

No architecture replacement, new core/firmware installation, additional platform qualification, save migration, library corpus scan, preference redesign, cross-platform deployment, or blanket game-compatibility claim. Existing accepted artwork and presentation authority are retained; the Genesis correction only restores the required frontend projection transform.

## Genesis projection correction (2026-09-29)

The custom Genesis passthrough shader assigned `gl_Position = Position`, omitting RetroArch's supplied model-view-projection matrix. That violates the frontend vertex-coordinate contract and matches the reported inverted image occupying a viewport quadrant. It now declares the standard `MVP` uniform and uses `gl_Position = global.MVP * Position`. Texture coordinates, package aperture, contain policy, core options and artwork are unchanged. This restores the frontend projection; it adds no game-specific geometry or manual rotation.

Reference: [Libretro Slang specification and example](https://github.com/libretro/slang-shaders/blob/master/README.md).

The existing native shader deployment service deployed the repository correction to the canonical Genesis package. The original deployed source is retained at `build/milestone5/genesis-shader-before-mvp.slang`. Genesis package/deployment regression checks: **37 passed**. Corrected live evidence: `build/milestone5/genesis-03-mvp/` (20.020 seconds alive, Stop/shutdown passed, no owned groups or transient files remaining, persistent source config unchanged). The user explicitly confirmed correct orientation and placement.

## Reopened bezel-selection audit

The qualification script now retains the final layered `input_overlay` selection,
its descriptor and artwork hashes, relevant viewport settings, and a copy of the
exact launch-selected PNG before session cleanup. Two regressions verify that later
append configs supersede a stale primary overlay and that disabled overlays do not
read stale paths. Focused runtime/lifecycle/launcher suite: **99 passed**.

All three fresh runs selected the approved artwork: Genesis and NES used temporary
adaptive frames generated from the updated packages; SNES selected the approved
installed PNG directly. Genesis ran 20.021 seconds, NES/SNES each 10.010 seconds.
All stopped and shut down successfully, preserved persistent configuration and left
no owned process group, cleanup error or transient file. Evidence lives under
`build/milestone5/bezel-audit-{genesis,nes,snes}/report.json` and `selected-overlay.png`.
These PNGs are launch-selected assets, not screenshots of the emulator display.

An older NES PNG also exists in RetroArch's separate Flatpak configuration tree.
It is not selected by these audited RetroVault launches. No root cause for the
user-reported discrepancy is yet established. The user has been asked whether the
old image appears through RetroVault Library, direct RetroArch, or a preview, and
for one affected game. Do not close the reopened issue until that path is resolved.

## Genesis Library-path resolution

The user narrowed the report to Sonic on Genesis and explicitly confirmed NES/SNES
work correctly. Root cause: `platform.sega.genesis` lacked `extensions` in RVDB YAML
and the generated bundle. The actual Library scanner returned the display name
Sega Genesis with an empty canonical platform ID. CoreMapper's legacy name mapping
still selected Genesis Plus GX, allowing launch, but the production presentation
resolver correctly did not assume Genesis from a multi-system core. Consequently
no canonical Genesis bezel was selected through that Library path. Earlier live
qualification supplied the canonical ID explicitly and masked the defect.

Correction: add `md` and `gen` to the existing RVDB platform source, rebuild through
the validated producer, synchronize the consumer bundle. No scanner fallback,
core-to-platform guess, shader change or NES/SNES modification was introduced.
Evidence for these core-supported formats: https://docs.libretro.com/library/genesis_plus_gx/#extensions
Shared binary/disc/archive extensions were deliberately not assigned to Genesis.

A real-bundle regression failed with the empty ID before the fix and now passes for
`.md`, `.gen`, and `.MD` through scan, core mapping and production-package selection.
The qualification runner now requires Library RVDB extension identification and
rejects unidentified/mismatched content, rather than injecting the requested ID.
A stale host-dependent package test was corrected to use repository fixtures and
the approved Genesis aperture. RetroVault full suite: **1,971 passed**; RVDB: **376
passed**. Source and consumer bundle SHA-256:
`0c32be3117d31830c5c2e4a8554b2c2f627ed7474c81dbc1697511e5afbf3b9a`.

Actual Sonic scan now returns `platform.sega.genesis` and
`genesis_plus_gx_libretro.so`. Live evidence:
`build/milestone5/genesis-library-fixed/report.json` and `selected-overlay.png`.
The metadata-derived launch selected the approved adaptive bezel, ran 20.020 seconds,
then passed Stop/shutdown, no remaining process/transients, and persistent config
preservation. These remain process/asset observations, not claimed human screenshots.
Existing windows retain the old RVDB snapshot until application restart. The user
has been asked to restart and confirm Sonic's bezel before final visual reclosure.


## Final user acceptance and reclosure — 2026-09-29

The user confirmed: “Everything runs Exactly as it's supposed to” and authorized
reclosure and progression to the next milestone. This resolves the pending Genesis
Library-path visual confirmation. NES/SNES acceptance remains intact. Milestones
#5 and #6 are complete within their approved scope; no required work remains.
Verification remains 1,971 passing RetroVault tests and 376 passing RVDB tests,
plus the recorded bounded runtime and cleanup checks. No new runtime change was
made during this documentation-only reclosure. Milestone #7 awaits its scope.
