# Milestone #6 — Approved bezel integration and closure

Current audit status: **COMPLETE — re-closed with user visual confirmation, 2026-09-29.**
The user confirmed that everything runs exactly as intended after the Genesis
Library metadata correction and explicitly authorized reclosure. Earlier audit
and pending statements below describe historical checkpoints, not outstanding work.

Closed 2026-09-29 following the user's approval of the final NES, SNES and Genesis
artwork and explicit request to integrate it and close the milestone.

## Delivered assets

- NES: paired red rules beside RetroVault; existing Nintendo ® retained.
- SNES: existing paired purple rules retained; platform ® added; RetroVault ® removed.
- Genesis: original Model 1 design with paired gold rules, Sega Genesis ® and no
  RetroVault legal symbol. The source design, branding revision and production
  normalization are reproducible and retained under `design/` and `tools/`.

NES/SNES viewport pixels and alpha are unchanged by branding edits. Genesis is a
1920×1080 RGBA package with physical aperture X312 Y80 W1296 H770. Transparent
source artifacts are composited onto black outside the exact transparent opening.
The existing AdaptiveBezelRuntime fits only the inner artwork frame around the
contained core-reported viewport. Logos, controls and outer housing remain fixed.
At the existing 1.524 reference aspect, containment is X373 Y80 W1173 H770.
This reference is evidence, not a hard-coded per-game runtime override.

The package manifest and presentation specification agree. Stale specification
flags that said UNCONFIGURED/incomplete now reflect the existing READY policy and
complete package. The former placeholder generator now normalizes the approved
source, so rebuilding does not restore the obsolete artwork.

## Verification and deployment

- Full RetroVault suite: **1,967 passed**, including three added Genesis adaptive
  frame cases covering 1.524, 1.306 and 4:3 aspects, exact alpha and unchanged outer art.
- After final transparent-RGB cleanup: **18 focused tests passed**.
- All three overlays deployed using the existing NativeVisualDeploymentService.
  Every installed package file was compared byte for byte with its repository source.
- Previous installed packages retained in `build/milestone6/before-approved-bezels/`.
- Deployment hashes: `build/milestone6/final-deployment.json`.
- Full test output: `build/milestone6/final-automated-tests.log`.
- Sequential live production runs: `build/milestone6/final-{genesis,nes,snes}/report.json`.
  Each stayed alive for 10.010 seconds, stopped successfully, shut down successfully,
  and left no owned process group, temporary files or cleanup errors.
- Runtime logs contain no ERROR/WARN entries. Each persistent RetroArch config hash
  remained `df6aff21b9193f3a1e90420ce0255be14e4bf8255fdfb0e7fc96f96b9dfd064d`.

The user's final artwork approval is the visual acceptance for this extension.
The qualification runner's `visual_acceptance: pending` is retained verbatim because
it only records process evidence; these runs are not represented as an additional
human gameplay inspection. Prior Milestone #5 runtime visual acceptance is historical.

## Preserved boundaries and scope

RVDB knowledge, local library identities, user persistence, presentation precedence,
core selection, shader processing (including the Genesis orientation fix), process
ownership and cleanup retain their existing architecture. Changes are confined to
approved presentation assets, package geometry/metadata, reproducible asset tooling,
regression expectations and closure documentation. No user saves or persistent
RetroArch settings were changed. No commit or push was performed.

Continuous mid-session geometry adaptation, additional platforms, new shaders,
long-session/all-game qualification and later milestones remain outside scope.
Milestone #6 is complete within the approved scope. Milestone #7 has not started.

## Genesis-only report resolved in metadata

The user confirmed NES/SNES work correctly. Genesis Library identification was
missing because RVDB had no `md`/`gen` extensions for that platform. The correction
is documented in [Milestone #5](milestone5_runtime_qualification.md#genesis-library-path-resolution).
Approved artwork remains unchanged. Final tests and metadata-derived Sonic launch
pass; user confirmation after restarting the application is pending.


## Final user acceptance and reclosure — 2026-09-29

The user confirmed: “Everything runs Exactly as it's supposed to” and authorized
reclosure and progression to the next milestone. This resolves the pending Genesis
Library-path visual confirmation. NES/SNES acceptance remains intact. Milestones
#5 and #6 are complete within their approved scope; no required work remains.
Verification remains 1,971 passing RetroVault tests and 376 passing RVDB tests,
plus the recorded bounded runtime and cleanup checks. No new runtime change was
made during this documentation-only reclosure. Milestone #7 awaits its scope.
