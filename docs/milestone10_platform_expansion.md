# Milestone #10 — Platform expansion

Approved scope: extend the complete NES pipeline qualification to SNES and Genesis,
retaining NES as the regression baseline. No new hardware platform is being added.
Implementation, automated tests and live technical qualification are complete.
Human acceptance is recorded separately below. **Milestone #10 is complete and
formally closed.**

## Implementation and ownership

`scripts/qualify_retroarch_runtime.py` now carries the selected platform through
source registration, real Library scanning, persistence, launch and the separate
restart interpreter. Its small qualification case table supplies only a label and
an existing visual catalog reference. Existing READY policy, RVDB extension
resolution, core resolution and production-package validation remain authoritative.
Unsupported targets, ambiguous extensions, mismatched content and archives fail
before execution. Existing bounded runtime modes remain supported.

| Boundary | Existing owner and unchanged responsibility |
| --- | --- |
| RVDB knowledge | RVDBLibraryResolver supplies canonical platform/extension/core knowledge; bundles and producer sources are unchanged. |
| Local library state | ImportSourceStore, LibraryController, LibraryService, RomScanner and IdentityRegistry discover/register real files and preserve platform-specific local identity. |
| User persistence | LibraryState, CollectionStore and PresentationStore retain favorites, history, collections and saved preferences in existing formats. |
| Presentation resolution | LibraryPresentationStudioService, PresentationCompositionFactory, PlatformPresentationPolicyRegistry and CanonicalProductionPackageResolver resolve the platform's approved package without rewriting saved preference. |
| Runtime configuration | Existing RetroArch configuration builders compose isolated primary/session/overlay/shader settings. |
| Emulator execution | GameLaunchController, CoreResolver, ProcessLifecycleAdapter and RetroArchLauncher retain validation, history callback and process/cleanup ownership. |

No production service or UI change was needed. Sharing Genesis Plus GX does not
qualify Master System, Game Gear or SG-1000, nor let them borrow the Genesis package.
A missing canonical game match remains legitimate: local file and platform identity
are sufficient for these existing launch paths.

## Verification matrix

| Platform | Automated file formats | Qualified core | Live content |
| --- | --- | --- | --- |
| NES | `.nes` | FCEUmm | Duck Tales 2 |
| SNES | `.sfc`, `.smc` | Snes9x | Street Fighter II Turbo (`.sfc`) |
| Genesis | `.md`, `.gen` | Genesis Plus GX | Sonic the Hedgehog (`.md`) |

`tests/test_platform_pipeline.py` replaces the NES-only test module and runs the
existing success, failure, cancellation, history, persistence, UI handoff and fresh
restart cases across all five format cases. Mixed-platform tests use identical
names and bytes to verify independent identities, families, favorite/collection
membership, presentation and history across a fresh restart. Additional checks
cover incompatible cores and foreign production manifests.

`tests/test_library_rvdb_scanner.py` verifies all five canonical format mappings and
leaves ambiguous `.bin` unresolved. `tests/test_launch_presentation_resolution.py`
verifies that unconfigured Sega platforms cannot inherit Genesis presentation.
`tests/test_runtime_qualification.py` verifies unsupported qualification targets.

Full suite: **2,118 passed in 35.28 seconds**
(`build/milestone10/automated-tests.log`). Focused pipeline/runtime checks: 106 passed;
scanner/presentation boundary checks: 36 passed. Compilation and diff checks passed.
Synthetic alternate-extension tests do not claim live compatibility with every ROM.

## Reproduce the live pipeline

Use an existing user-owned ROM of the selected platform and a new output directory:

```bash
PYTHONPATH=/home/oilcan/retrovault /home/oilcan/retrovault/.venv/bin/python -B \
  -m scripts.qualify_retroarch_runtime --pipeline --platform snes \
  --rom '/absolute/path/to/game.sfc' \
  --output '/absolute/path/to/new-qualification-directory' --seconds 30
```

Use `--platform nes` with `.nes`, or `--platform genesis` with `.md`/`.gen`.
SNES also accepts `.smc`. The runner stages a ROM copy and isolates XDG configuration,
cache and data. It exercises the real scan and stores, records successful-launch
history, stops the emulator, and reconstructs the persisted state in a fresh process
from an unrelated working directory. It guards the original ROM, primary config,
installed bundle and existing user JSON files, and checks for unexpected new files.

Passing live reports are retained under `build/milestone10/nes-live/report.json`,
`build/milestone10/snes-live/report.json` and
`build/milestone10/genesis-live-repeat/report.json`.

NES passed 15.017 seconds; SNES passed 30.031 seconds; Genesis passed 30.032 seconds.
Every stage passed, including real history persistence, exact fresh-process state
restoration, Stop/shutdown and cleanup. Each run preserved all eleven protected
files, with hashes rechecked afterward, and added no user JSON files. Selected
artwork and effective settings match Milestone #8 (ignoring the temporary overlay
pathname). No warnings, owned process groups or temporary session resources remained.
The first Genesis attempt exited after 16.319 seconds; the user confirmed an
accidental manual closure. That report is retained but is not counted as passing.
The aggregate `build/milestone10/acceptance-evidence.json` records technical results,
comparison with approved artwork/settings and separate human acceptance.

## Acceptance and limits

The user confirmed SNES worked “100% coorectly” and explained the first Genesis
exit was accidental. For the repeated Genesis run, the user confirmed:
"It looks 100% correct! Ready to close". Both visual/gameplay acceptance items are
closed, recorded separately from the original machine reports.
Process success and matching configuration/artwork hashes do not establish visual
correctness or input behavior.

Outside scope: additional hardware platforms, READY promotions, core installation,
new artwork/shaders, RVDB schema or source changes, persistence migrations, archive
support expansion, UI redesign, exhaustive game compatibility and Milestone #11.
Existing assets, platform policies and production architecture remain unchanged.

Remaining approved work: **none**. Milestone #11 has not started.
