# Milestone #12 — Advanced visuals

Approved scope: bounded CRT adjustments for existing NES, SNES and Genesis production
packages, retaining package selection and geometry authority. Implementation and
technical qualification and human visual acceptance are complete.
**Milestone #12 is formally closed.**

## Controls and ownership

`services/presentation/visual_tuning.py` defines the package-specific capability
contract. NES/SNES expose brightness (`post_br`, 0.5–3.0) and mask strength
(`maskstr`, 0–1). Genesis exposes brightness (`RVV_BRIGHTNESS`, 0.5–2), mask strength
and scanline strength (both 0–0.5). These are bounded subsets of the supported shader
parameters, not a generic parameter editor. Numeric suggestions in Custom mode do
not claim to be dynamically discovered shader defaults.

Production package resolution still selects the shader and overlay. Adjustments
cannot choose a replacement shader, modify geometry or make an unconfigured platform
READY. Local cover artwork, RVDB knowledge, core policy and file identities remain
separate. No RVDB schema, source or bundle changes are needed.

Presentation Studio offers game/platform scopes, a supported control selector and:

- **Inherit:** remove this scope's value; a game then inherits the platform choice.
- **Approved appearance:** explicitly use the package's own behavior for that control,
  suppressing any inherited platform adjustment at game scope.
- **Custom:** save a finite value within the supported range.
- **Restore approved appearance:** clear platform tuning at platform scope, or explicitly
  suppress all supported inherited controls for the selected game at game scope.

Saving affects the next launch; an active emulator is not hot-reloaded. Effective
value/source is shown. Controls are displayed only for an available production
package. UI widgets call LibraryPresentationStudioService and never edit shader files.

## Persistence and launch contracts

PresentationStore version 3 adds an optional `visual_tuning` section to the existing
file. Versions 1 and 2 remain readable without writing during load. Platform keys are
canonical IDs. Game keys use durable local-file IDs and include their canonical
platform; a platform mismatch fails rather than applying another system's values.
Existing shader/overlay/artwork assignments and quarantined legacy conflicts survive
adjustment writes, and existing assignment writes preserve tuning. No second settings
store was introduced. Earlier app versions cannot read the new version-3 document.

PresentationCompositionFactory supplies saved tuning to LaunchPresentationResolver.
The launch decision carries semantic values separately from selected asset references.
GameLaunchController passes them through LaunchProfile. RetroArchLauncher independently
requires a validated production package and validates values before archive resolution
or process creation. Unknown controls, booleans, non-finite values and out-of-range
values are rejected. Only allowed CRT parameter names can be generated.

ShaderRuntimeConfig remains the generic transient-preset serializer. Package sidecar
parameters are retained, and validated tuning overrides only the named CRT controls.
Both content probing and final execution receive the same parameter mapping. The
source presets and persistent RetroArch configuration are not edited by tuning.
Runtime values containing newlines or NUL are rejected before serialization.

## Package changes

- SNES: the `.shader.cfg` sidecar now uses `HSM_ASPECT_RATIO_MODE = 6`, matching the
  existing preset and viewport-following contract. Previously the sidecar overwrote
  mode 6 with mode 0. Live qualification verifies the final wrapper, not just a source
  preset in isolation.
- Genesis: opt-in brightness, RGB-column mask attenuation and source-row scanline
  attenuation were added to the existing shader. Brightness defaults to 1; both effect
  strengths default to 0. The MVP orientation correction and source texture coordinates
  are unchanged; this shader still does not crop, stretch or reposition gameplay.
- NES: its package files remain unchanged.

The SNES overlay package and Genesis shader package were installed through the existing
NativeVisualService. Seven original installed files and their hashes were backed up
under `build/milestone12/deployment-backup/`. External Mega Bezel sources were not edited.
Approved bezel images and logos are unchanged.

## Verification and evidence

Full automated suite: **2,166 passed** (`automated-tests.log`).

Automated tests cover version compatibility, retained assignments, reset/inheritance,
range checks, unsupported controls, wrong-platform state, UI operations, fresh-process
pipeline restoration and independent launch rejection. A dedicated composition test
asserts identical probe/final parameters while retaining protected geometry values.

Evidence resides in `build/milestone12/`:

- `automated-tests.log`: full suite.
- `final-focused-tests.log`: 168 passing tuning/platform/launcher checks.
- `studio-review.png`: isolated Qt UI inspection, not user acceptance.
- `{nes,snes,genesis}-{default,adjusted}/report.json`: bounded live pipeline evidence.
- `acceptance-evidence.json`: aggregate technical and human acceptance record.

The runner's `--visual-tuning-json` option writes only to its isolated pipeline profile.
It captures the actual shader preset before cleanup and includes effective tuning in
its fresh-process restart snapshot. For example, with the existing `--pipeline`, ROM,
output and platform arguments, add:

```text
--visual-tuning-json '{"brightness":1.15,"mask_strength":0.4}'
```

All six live sessions passed their 30-second observation interval, all pipeline
stages, exact fresh-process state restoration and cleanup. Logs contained no shader
errors. Approved bezel hashes and effective viewport settings match Milestone #10;
the SNES shader wrapper additionally proves mode 6 after sidecar composition.
Protected ROM/configuration/bundle/user JSON hashes were rechecked after the runs.
Both deployed packages report CURRENT, and RVDB producer/consumer hashes still match.

After each adjusted run, its isolated profile was reset and reconstructed in a fresh
interpreter. Tuning was removed while identity, favorites, collections, history and
saved asset preferences were preserved. This is a reset/state check, not a claim of
an additional post-reset live visual session. Original live reports are retained;
subsequent reset snapshots live in each adjusted directory's `reset-evidence.json`.

The user accepted the default and adjusted visual/gameplay sessions with "I approve"
in response to the final acceptance request. Human acceptance is recorded separately
from process, parameter and shader-compilation evidence.

Remaining approved work: **none**. Milestone #12 is complete and formally closed.
Milestone #13 has not started.

## Limits

No new bezel designs, animated indicators, HDR, rotation, widescreen hacks, generic
third-party shader editor, live shader preview/hot-reload, online downloads, new
platforms or Milestone #13 work. The new Genesis treatment is deliberately simple;
it does not claim phosphor-accurate CRT simulation or performance on untested hardware.
