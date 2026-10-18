# USQE Milestone #8 — Presentation families and reusable templates

Status: **COMPLETE within the approved scope, including the startup-probe extension.**
The user accepted the corrected Genesis run and authorized publication of the
accumulated tested work. Milestones #9–#12 remain unstarted.
Earlier pending entries below describe intermediate checkpoints; the final
acceptance and publication checkpoint at the end supersedes them.

## Approved boundaries

Preserve the existing presentation architecture and qualified NES/SNES/Genesis
packages. Qualify reusable family envelopes separately from concrete
platform/backend/package/content/display bindings. No readiness promotion, RVDB
change, geometry recalibration, new platform support or live geometry switching.
No existing user configuration/save/preference is migrated. Earlier M6/M7 work
remains in the shared worktree and is not republished by this milestone.

The bounded live batch is classic 4:3, in order: NES/FCEUmm, SNES/Snes9x libretro,
Genesis/Genesis Plus GX. Only one representative content mode and the observed
host display are covered per case. The batch has no widescreen or mixed members;
these empty categories do not require inventing a platform. Native Snes9x keeps
its separately qualified native display; RetroArch templates do not apply to it.
Master System and conditional SG-1000 remain Milestone #9 candidates only.

## Existing authorities retained

- `MasterPresentationProfileRegistry`: reusable family envelopes and CONTAIN math.
- `PlatformPresentationPolicyRegistry`: existing explicit platform-family binding.
- `CanonicalProductionPackageResolver` / `ProductionPresentationPackageValidator`:
  exact approved platform package; unconfigured platforms cannot borrow one.
- `ProductionGlassResolver`: actual package aperture, distinct from family bounds.
- `CoreDisplayAspect` / `ContentLoadedDisplayAspectProbe`: core-authoritative
  display aspect observed after content load, not guessed from framebuffer shape.
- Existing launcher, transient configuration composition and owned-process cleanup.
- `PresentationStore` and composition factory: existing preference authority.

`MasterPresentationQualification.QUALIFIED` retains its existing meaning: a
physical family envelope exists. It is not a new assertion that all bindings,
versions, displays or content modes passed live qualification. The new records
are evidence only; application launch/readiness policy does not consume them.

Protected package apertures, all on a 1920×1080 canvas:

| Platform | X | Y | Width | Height |
| --- | ---: | ---: | ---: | ---: |
| NES | 355 | 100 | 1206 | 762 |
| SNES | 438 | 71 | 1044 | 783 |
| Genesis | 312 | 80 | 1296 | 770 |

The generic classic family is `(240, 0, 1440, 1080)`. It must never replace these
package apertures. Family membership does not require identical artwork geometry.

## Implemented changes

1. Reject non-finite aspect inputs in `master_profile.py`, `display_aspect.py` and
   `contain_runtime.py`. NaN/infinity previously passed positive-number checks
   and failed later during integer conversion. Existing valid geometry is retained.
2. `services/presentation/qualification.py` assembles mathematical family examples,
   snapshots package/core hashes and binding facts, compares the captured final
   viewport against containment within the actual package aperture, and assesses
   evidence completeness. It never writes policy or changes readiness.
3. `capture_presentation` in the existing runtime runner now retains ordered
   configuration contents/hashes, orientation/bias/aspect/display directives and
   the runtime shader-preset hash. These are configuration evidence, not screenshots.
4. `scripts/qualify_presentation_families.py` is a thin wrapper around the existing
   isolated production pipeline. Its default operation writes mathematical
   templates only. Explicit `--live` uses the established Library/controller/
   launcher, managed keyboard and cleanup path. Reports include core and frontend
   launcher hashes, loaded RetroArch version, driver log evidence, display facts,
   content mode and user acceptance fields. A frontend launcher may be a wrapper;
   its checksum is not mislabelled as the loaded Flatpak executable checksum.

The wrapper's exit code reflects automated runtime/geometry success, not overall
visual qualification. `assessment.result` remains not-run/blocked until the
required evidence and genuine human observations are present. Multiple/headless
Qt screens do not yield invented output dimensions. Single-screen Qt inventory
records physical-pixel dimensions derived from size and device-pixel ratio;
targeted visual acceptance remains required for the actual game output.

The post-run observed aspect is compared to startup-composed viewport geometry.
A later conflicting geometry event fails that comparison; it does not silently
qualify switching. Observing a SET_GEOMETRY event is not transition acceptance.

## Reusable case template

| Field | Required evidence |
| --- | --- |
| Identity | Case ID, canonical platform, registered physical ID, loose content SHA-256, explicit content mode |
| Binding | Backend/core, core binary checksum, family envelope, separate package aperture |
| Runtime | Loaded frontend version, configured launcher checksum, OS and driver evidence |
| Display | Width, height, scale and provenance; missing/ambiguous data blocks qualification |
| Package/config | Package-local assets/dependencies hashed; ordered launch configuration and runtime shader/artwork hashes retained |
| Geometry | Observed core display aspect, expected package containment, captured viewport, bounds/rounding checks |
| Lifecycle | Launch, Stop, shutdown, preservation and cleanup from existing runner; fresh-process Library reconstruction separately labelled |
| Human checks | Upright orientation, all intended edges, natural proportions, bezel alignment, startup and gameplay; original observation/date |
| Result | pass / fail / blocked / not_run / not_applicable with scope and limitations |

The current runner reconstructs Library state in a fresh process; it does not
claim a second visual emulator run. Prior live restart evidence remains scoped to
its original case. A second visible launch is required if fresh presentation
repeatability cannot otherwise be established for the tested case.

## Family/batch matrix

| Family | Template evidence | This milestone's live batch |
| --- | --- | --- |
| CLASSIC_4_3 | Existing envelope, calculated containment examples | NES and SNES accepted; Genesis pending |
| WIDESCREEN_16_9 | Existing envelope, calculated examples only | Not applicable: no selected wide-content binding |
| Mixed/exception | Explicit-mode/transition evidence requirements | Not applicable: no selected mixed binding |
| ARCADE_VERTICAL | Existing envelope, calculations only; rotation not newly qualified | Outside bounded live batch |
| Handheld / horizontal arcade / dual-screen / specialized | Existing capability-only classification retained; no invented physical layout | Outside bounded live batch |

All mathematical rows have `live_result: not_run`; generic registry labels are
reported separately. No wide/vertical/handheld platform is promoted by this table.

## Verification so far

- Regression-first reproduction: **15 failed, 57 passed** before finite-value fix
  (`build/usqe8/nonfinite-before.log`). Negative infinity already rejected but did
  not satisfy the new consistent finite-input diagnostic.
- Corrected geometry set: **72 passed**.
- Initial full suite: **2,440 passed** (`build/usqe8/full-suite.log`).
- Updated focused evidence/geometry/runtime set: **117 passed**
  (`build/usqe8/focused-final.log`).
- Final full suite: **2,445 passed** (`build/usqe8/full-suite-final.log`).
- Mathematical templates: `build/usqe8/family-templates.json`.
- Binding snapshots: `build/usqe8/binding-baselines.json`.
- Protected checksums: `build/usqe8/protected-baseline.json` (47 files).
- NES/Kirby live automated checks passed for the 30-second run on a single
  1920×1080 display at scale 1.0. Captured viewport matched package containment;
  Stop/shutdown succeeded with no owned process or transient artifacts remaining.
  All 47 protected checksums remain unchanged. Evidence:
  `build/usqe8/nes-classic-live-20261017/presentation-qualification.json`.
- NES/Kirby and SNES/Super Mario Kart human visual checks were accepted by the
  user: “Yes, all visual checks passed” for each run. Both scoped assessments
  pass. Original observations and timestamps are retained in each case record.
- SNES automated geometry, pipeline and cleanup checks passed with no remaining
  owned process or transient artifacts. Evidence:
  `build/usqe8/snes-classic-live-20261017/presentation-qualification.json`.
- Genesis/Sonic attempt did not pass: the process exited at 23.223 seconds,
  before the 30-second deadline. The log recorded a later geometry event with
  aspect 1.306, requiring `(457, 80, 1006, 770)` containment, while the startup
  viewport remained `(373, 80, 1173, 770)`. The user confirmed “I closed it; the picture looked correct,” explaining
  the early exit. The startup-to-runtime geometry discrepancy still requires
  investigation; no geometry or production assets have been changed.
  Cleanup passed, package hashes and all 47 protected checksums remain unchanged.
  Evidence: `build/usqe8/genesis-classic-live-20261017/presentation-qualification.json`.
  This unsuccessful attempt is retained and does not qualify Genesis.

## Live procedure and pending evidence

Use user-owned disposable ROM copies through `--live`, with explicit normal
startup/early-gameplay content mode. Inspect upright orientation, all intended
edges, natural proportions, bezel alignment and startup. Existing CRT treatment
and approved packages remain unchanged. Each bounded run is followed by actual
user observations; process success alone cannot pass it. Exact display facts,
case-specific runtime records and human results remain pending.

Example invocation (requires a user-ready live session):

```sh
.venv/bin/python -m scripts.qualify_presentation_families --live \
  --platform nes --rom /absolute/path/to/owned-game.nes \
  --content-mode 'normal startup and early gameplay' \
  --output build/usqe8/nes-case --seconds 30
```

Closure requires complete focused/full regression results, unchanged protected
packages/user data/bundles, explicit evidence limits, accepted targeted 4:3 batch
observations, clean diff integrity and final user review. No live wide/mixed or
other-family acceptance is inferred. No commit, push or Milestone #9 work is
part of this implementation turn.

## Additional finding — Genesis startup geometry timing

A bounded headless diagnostic reproduced initial geometry at 0.181 seconds
(256×192, aspect 1.524) and content geometry at 0.445 seconds
(320×224, aspect 1.306). The existing 0.20-second settling rule can return
between these events. The diagnostic used a copy of the installed core options
and isolated output, and its owned process was terminated/reaped afterward.
Evidence log: `build/usqe8/genesis-headless-diagnostic/retroarch.log`.
This establishes a startup acquisition race; it does not establish a need for
mid-game switching or package recalibration.

User-approved scope extension, now implemented: keep acquisition open through
its existing bounded timeout (default two seconds), retaining the latest valid
core geometry, rather than returning on an early quiet interval. Added focused
regressions for a later event after that interval and initial-only cores, preserve
process ownership/cleanup, then repeat controlled checks, the full suite and
Genesis visual qualification. Expected tradeoff: additional startup latency,
up to the existing timeout. No arbitrary delay guarantees all future content
modes; qualification remains scoped to observed cases. The probe and its regression tests now implement this bounded correction.
The `settle_time` constructor argument remains accepted for caller compatibility,
but no longer shortens the observation window. Existing process-exit handling
and process-group cleanup remain unchanged.

Regression-first timing checks: **2 failed, 8 passed** before the fix.
After the fix, **128 focused tests passed** using isolated XDG directories and
Qt offscreen. A headless check with the actual Genesis core returned aspect
1.306 in 2.121 seconds, with no owned process or temporary files remaining
(`build/usqe8/genesis-headless-diagnostic/fixed-probe-result.json`).
An initial test invocation lacked Qt offscreen, and a subsequent invocation
used the read-only default cache; those attempts are retained separately and
are not counted as successful verification. The correctly isolated full suite passed **2,448 tests** in 48.34 seconds
(`build/usqe8/full-suite-probe-window-isolated.log`). The repeated Genesis
run completed 30.033 seconds, with aspect 1.306 and viewport
`(457, 80, 1006, 770)` matching package containment. All pipeline stages passed;
no owned process, transient artifacts or cleanup errors remained. All 47
protected checksums remain unchanged. Evidence:
`build/usqe8/genesis-classic-fixed-live-20261017/presentation-qualification.json`.
Human acceptance of this corrected run remains pending. Compile and diff
whitespace checks passed. No commit or push has been performed.

## Final acceptance and publication checkpoint

The user confirmed the corrected Genesis run with “Yes, all visual checks
passed”, in response to the six explicit visual checks. NES/Kirby and SNES/Super
Mario Kart received the same explicit acceptance. All three scoped assessments
pass for their recorded core, package, fixture, content mode and 1920×1080 display
at scale 1.0. The unsuccessful first Genesis attempt remains in the evidence.

Final regression: **2,448 passed**; focused startup-probe/runtime checks:
**128 passed**. Compile/import and Git whitespace checks passed. The corrected
Genesis pipeline completed 30.033 seconds and cleaned up all owned processes and
transient artifacts. All 47 protected checksums match the pre-milestone snapshot.
Canonical/installed RVDB bundle SHA-256 remains
`4d99f2b1bff694f26ca1b1ff68b7d4d1816236abb1e64d10a62e14bf20e3eb43`.

The user authorized committing and normally pushing accumulated tested work from
Milestones #6–#8. This publication includes the controller and save/recovery work
previously retained locally. It excludes ROMs, saves, generated build evidence,
user configuration, external emulator files and production artwork. Historical
closure records remain unchanged. The prior RetroVault checkpoint is
`e7f18f046eeed0b859c7601e25983cf7e4637dc5`; RVDB remains unchanged at
`cc7b5e919f337910601738018b99c05007879c47`.

Remaining limits: physical gamepads remain unqualified; wide/mixed/other-family
live cases and mid-game geometry switching are not qualified; native Snes9x keeps
its separate display contract. No new platform is promoted. The bounded startup
window adds latency and does not promise to capture arbitrarily late transitions.
USQE #8 is complete within these limits; #9–#12 remain unstarted.
