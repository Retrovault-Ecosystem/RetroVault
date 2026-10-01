# RetroVault Current Milestone

Current status: **Milestone #13 — Standalone emulators — COMPLETE AND CLOSED.**

The approved native Linux Snes9x GTK SNES adapter is connected to shared session
ownership, Settings, selected-edition launch/history and capability reporting.
RetroArch remains the default. RVDB, physical identities, persistence formats and
qualified production assets remain unchanged. Final full suite: **2,198 passed**
(including **32 new standalone cases**). Both repositories pass diff integrity checks.

The corrected isolated qualification passed a 30-second SNES run, Stop,
fresh-interpreter relaunch and shutdown, with Library identity/history and protected
user files preserved. On 2026-10-01, the user confirmed picture, audio and gameplay
controls with “Everything Passes”. All approved Milestone #13 work is complete and
formally closed. Milestone #14 has not started. See [standalone emulator contracts](milestone13_standalone_emulators.md).

## Milestone #12 closure (historical)

Current status: **Milestone #12 — Advanced visuals COMPLETE AND CLOSED.**

Bounded platform/game CRT adjustments use the existing PresentationStore and
production launch pipeline. Older state remains readable; game adjustments use
durable local-file identities. Approved appearance and inheritance are explicit.
NES/SNES offer brightness and mask controls; Genesis adds opt-in brightness, mask
and scanline treatment with neutral defaults. The SNES sidecar now follows its
preset’s viewport authority. Bezel artwork, RVDB, core policy and Library covers
remain unchanged.

Full suite: **2,166 passed**; final focused checks: **168 passed**. All six default/adjusted
30-second sessions passed, with shader compilation, restart, reset, preservation and
cleanup evidence recorded. The user accepted both default and adjusted visual/gameplay
runs with "I approve". All approved work is complete; Milestone #12 is formally closed.
See [advanced visual contracts](milestone12_advanced_visuals.md).
Milestone #13 subsequently began with the approved scope recorded above.

## Milestone #11 closure (historical)

Current status: **Milestone #11 — Metadata/artwork COMPLETE AND CLOSED.**

Conservative RVDB title enrichment and platform-aware local cover resolution now
reuse the existing resolver, scanner, classifier and artwork service. Refresh
preserves explicit cover intent and per-edition artwork; Library and Playlists
refresh together. Metadata is rendered as literal text. No RVDB data, durable
formats, runtime configuration, core policy or approved presentation assets changed.

Verification: **2,142 automated tests passed**, including fresh-process metadata,
artwork and user-state restoration. An isolated Qt UI review verified cover aspect
ratio and metadata rendering. Existing missing catalog entries and local covers
remain absent; no downloading or invented metadata is implied.

See [metadata/artwork contracts](milestone11_metadata_artwork.md) for evidence and
limits. All approved Milestone #11 work is complete and formally closed following
the final evidence audit and the user’s closure request. No approved work remains.
Milestone #12 subsequently began with the approved scope recorded above.

## Milestone #10 closure (historical)

Current status: **Milestone #10 — Platform expansion COMPLETE.**

The approved scope extends the complete NES pipeline to SNES and Genesis. Existing
production services, RVDB data, platform policies, persistence formats and approved
assets remain unchanged. The runner and tests now cover all three platforms, with
five file-extension cases, mixed-platform isolation and fail-closed boundary checks.

Full suite: **2,118 passed**. NES (15 seconds), SNES (30 seconds) and Genesis
(30 seconds, repeated after accidental manual closure) passed every live stage.
Fresh-process state, protected files, approved artwork/settings and cleanup checks
passed for all three. The user accepted SNES visuals/gameplay and confirmed the
repeated Genesis run: "It looks 100% correct! Ready to close".
See [platform expansion qualification](milestone10_platform_expansion.md) for evidence
and limits. All approved Milestone #10 work is complete and formally closed.
Milestone #11 subsequently began with the approved scope recorded above.

## Milestone #9 closure (historical)

Current status: **Milestone #9 — One complete platform pipeline (NES) COMPLETE.**

The new `--pipeline` mode uses a real source registration and Library scan, durable
local-file identity, real favorite/collection/presentation stores, the production
launch controller, actual Recently Played persistence, and a fresh-process restart.
All state is exercised in an isolated profile using a copy of the user's NES ROM.

The integrated UI test exposed and fixed one production handoff: MainWindow now
passes the shared PresentationStore and launch resolver provider through PlaylistsPage
to GameDetails, matching the Library path. Existing architecture, RVDB source/bundles,
core policy, durable formats and approved assets remain unchanged.

Evidence: **2,035 full-suite tests passed**, followed by **28 final pipeline/runtime
checks** after the preservation guard was strengthened. The live NES run passed all
stages over 30.028 seconds, including Stop/shutdown, cleanup and fresh-process state
restoration. Eleven protected files remained unchanged; no user JSON files were added.
Selected artwork and effective presentation settings match the previous qualification.

See [NES pipeline qualification](milestone9_nes_pipeline.md) for the reproducible
command, failure cases, evidence and explicit limits. The requested repeat 30-second
run passed the full pipeline, and the user explicitly confirmed: "Yes, Visuals and
gameplay were correct!" Human acceptance is recorded separately from process evidence.
All approved Milestone #9 work is complete. Milestone #10 subsequently began with
the approved scope recorded above.

## Milestone #8 closure (historical)

Historical closure: **Milestone #8 — UI responsibility cleanup COMPLETE, 2026-09-30.**

The approved cleanup is implemented on the existing architecture:

- GameDetails delegates preparation, validation, launch/lifecycle coordination and
  successful-launch history to the Qt-independent GameLaunchController. Library and
  Playlists share that controller through MainWindow. Widgets retain dialogs/rendering;
  RetroArchLauncher retains independent execution validation and process ownership.
- Generated cheat inputs have explicit cleanup ownership, including failure and retry
  paths. The original user cheat database is not deleted. Partial serialization/write
  failures do not leave unowned input files.
- SettingsService owns executable/path checks, source-update construction and settings
  persistence outcomes. SettingsPage retains controls/signals and reports successful
  saves separately from failed post-save refreshes.
- LibraryPresentationStudioService supplies shared assignment commands and saved/effective
  state for Studio, Overlays, Shaders and Native Visuals. Production-package authority
  and explicit installation through NativeVisualService remain unchanged.
- LibraryService/LibraryController own Systems statistics. Unavailable collection/recent
  information is distinguished from zero; existing family/edition identity rules remain.

Verification:

- Baseline: **1,999 passed**. Final full suite: **2,020 passed** (`build/milestone8/automated-tests.log`).
- Final launch/UI/architecture checks after removal of workflow stdout diagnostics:
  **166 passed** (`build/milestone8/final-launch-tests.log`). Compilation and diff checks passed.
- NES, SNES and Genesis each ran for **15 seconds** from `/tmp` using the production
  GameLaunchController, presentation factory, lifecycle adapter and launcher. All passed
  Stop/shutdown, persistent-config preservation, one successful-launch history callback,
  and complete session cleanup. Reports: `build/milestone8/{nes,snes,genesis}/report.json`.
- Selected artwork hashes and effective presentation settings match the previously
  qualified Milestone #7 runs. The 12 checked user/configuration/artwork files remained
  unchanged. Evidence: `build/milestone8/acceptance-evidence.json` and
  `build/milestone8/preserved-files-before.json`.

Live reports establish process/configuration behavior, not new human visual acceptance.
No visual assets were changed. RVDB knowledge/bundles, durable storage formats, core
policy, source scanning, settings precedence and executable activation remain intact.
No new platforms, UI redesign, async scanning/probing, migrations or packaging were added.

See [architecture contracts](architecture_contracts.md#milestone-8--ui-responsibility-cleanup)
for owners and limits. All approved work in Milestone #8 is complete.
Milestone #9 subsequently began with the approved NES scope recorded above.

## Milestone #7 closure (historical)

Historical closure: **Milestone #7 — Configuration/startup reproducibility COMPLETE, 2026-09-30.**

Implemented anchored RVDB discovery, explicit validated bundle installation,
portable defaults, nested configuration validation, atomic persistence, shared XDG
path resolution, startup diagnostics, clear setting activation, and explicit primary
RetroArch configuration selection with isolated per-launch configuration.
The existing six-boundary architecture and durable user-data formats remain intact.

Verification: **1,999 tests passed** in the full suite; **82 Settings/startup tests
passed** after the final restart-notice correction. NES, SNES and Genesis bounded
production runs from `/tmp` passed lifecycle, persistent-config preservation and
transient cleanup checks. Selected artwork hashes and effective presentation
settings match the previously user-accepted baseline. This is configuration and
process evidence; no new human visual acceptance is inferred.

See [configuration/startup contract and evidence](configuration_startup.md).
Milestones #5/#6 remain closed, including the user-accepted Genesis Library fix.
The subsequent UI responsibility cleanup is recorded above.


## RVA1-C.15 — Live Library Refresh + Bulk Import Hardening

RVA1-C.15 establishes the production user-initiated Library refresh
workflow and hardens its interaction with RetroVault's existing Bulk
Import workflow.

The milestone builds on the protected RVA1-C.14 live source-reload
foundation. Library content can now be refreshed from configured
sources without restarting RetroVault while preserving the active
Library experience and synchronizing dependent application views.

### A.1 — User-initiated Library refresh

The Library exposes a production refresh action through its toolbar.

A refresh delegates to the existing Library controller reload boundary
rather than creating a second loading implementation.

After a successful reload, RetroVault synchronizes the dependent
Systems and Playlists views with the refreshed Library snapshot.

### A.2 — Library state preservation

Manual refresh preserves the active Library experience across the
reload boundary.

Protected state includes:

- search text;
- system filter;
- sort selection;
- favorites filter;
- recent filter;
- current Library view mode; and
- selected game when that game survives the reload.

If the selected system no longer exists, the system filter safely falls
back to All Systems.

If the selected game no longer exists, the details pane is cleared
instead of retaining stale game state.

The RVA1-C.14 identity-preserving reload contract remains intact for
surviving games.

### A.3 — Refresh status feedback

The Library toolbar exposes non-modal refresh status feedback.

During refresh:

- the refresh control is disabled;
- the status reports that the Library is refreshing; and
- no development error popup is introduced.

Successful refresh reports completion through the Library status
surface.

Expected refresh failures are contained and reported through the same
non-modal status boundary.

### A.4 — Refresh completion hardening

Application-level completion synchronization occurs only after the
Library snapshot has been refreshed.

Expected completion failures are contained without leaving the Library
control surface disabled.

A completion synchronization failure is represented as a partial
refresh rather than incorrectly reporting full success.

No new modal development-error path is introduced.

### A.5 — Refresh reentrancy protection

Manual Library refresh is serialized.

A second refresh request is ignored while a refresh is already in
progress.

All expected refresh completion paths clear the busy state and restore
the refresh control.

### A.6 — Refresh / Bulk Import serialization

Manual refresh and Bulk Import cannot execute concurrently.

While refresh is active:

- another refresh request is ignored; and
- Bulk Import is unavailable.

While Bulk Import is active:

- another Bulk Import request is ignored; and
- manual refresh is unavailable.

Cancellation of the Bulk Import directory chooser does not enter the
busy state.

Expected failure paths restore both controls.

### A.7 — Bulk Import completion containment

Bulk Import completion synchronization remains ordered after the
imported Library snapshot is applied.

Expected completion callback failures are contained.

On completion failure:

- the imported Library snapshot remains applied;
- the Bulk Import busy state is cleared;
- Library refresh and Bulk Import controls are restored;
- another Bulk Import can be attempted; and
- no new failure popup is introduced.

The existing production Bulk Import success and import-handler failure
dialogs remain preserved.

### A.8 — Bulk Import finalization safety

The Bulk Import post-handler boundary is protected by guaranteed
finalization.

Expected failures while applying or interpreting a Bulk Import result
are contained, including malformed result data and expected snapshot
processing failures.

The finalization contract guarantees:

- Bulk Import busy state returns to idle;
- Bulk Import control is restored;
- Library refresh control is restored; and
- the workflow can be retried.

The production Bulk Import success dialog remains available only after
successful result processing.

No additional failure popup is introduced by this hardening boundary.

### Protected application boundaries

RVA1-C.15 preserves the following established RetroVault contracts:

- RVA1-C.14 atomic live source reload behavior;
- surviving game object identity across source reloads;
- Library, Systems, and Playlists synchronization;
- existing production Bulk Import dialogs;
- protected Game Details production warning dialogs;
- collection and recent-game behavior;
- launch and lifecycle behavior;
- RVDB-backed canonical platform identity;
- existing RVV presentation and calibrated NES/SNES visual geometry.

### Closure validation

RVA1-C.15 closure validation established:

- C.15 targeted Library regression: 156 passed;
- RVA1-C.14 protected regression: 77 passed;
- protected modal-guard regression: 62 passed;
- complete RetroVault regression: 1273 passed;
- Python compile validation: PASS;
- Git diff integrity: PASS;
- local and remote protected checkpoint synchronization: PASS; and
- clean worktree: PASS.

No remaining C.15 hardening markers were detected at the closure
boundary.

### Technical closure checkpoint

The final technical implementation checkpoint before documentation
closure is:

`ebe4bba2725defcb9b8cc84ca6e82dd79d7cb7fb`

Commit:

`fix: finalize bulk import safely`

This checkpoint includes the complete RVA1-C.15 A.1 through A.8
implementation and regression contracts.

### Milestone status

**RVA1-C.15 is complete.**

The next RetroVault application milestone must begin from the protected
RVA1-C.15 documentation closure checkpoint.

## RVA1-C.16 — RetroVault Visuals Application Integration — COMPLETE

Protected technical checkpoint before closure:

`71dfd95d835a81b2882db1c0517fce174e57cd40`

RVA1-C.16 integrates the native RetroVault Visuals collection into
the production RetroVault application while preserving the shared
presentation architecture and RetroArch runtime composition path.

Completed contracts:

- RetroVault Visuals refresh through the native visual service boundary.
- Installation/update state and explicit installation confirmation.
- Default, canonical-system, and stable-game visual assignments.
- Clear/unassign support with natural presentation fallback.
- Direct Default/System/Game assignment visibility.
- Effective assignment visibility using production presentation
  precedence: game -> system -> default -> empty.
- Shared PresentationStore between the RVV page and production
  PresentationCompositionFactory.
- Production runtime composition consumes RVV assignments without a
  parallel presentation store.
- Current Library game context is shared with system/game assignment.
- Navigation refresh keeps visual discovery and assignment state current.
- Expected RVV operational failures are reported inline without error
  popups.
- Explicit install/update confirmation remains preserved.
- Existing shader, overlay, artwork, library, launcher, and presentation
  contracts remain protected.

Closure verification:

- C.16 targeted regression: PASS.
- Full RetroVault regression: PASS.
- Python compileall: PASS.
- Production RVV integration contract: PASS.
- Shared presentation-store contract: PASS.
- Runtime composition contract: PASS.
- Inline-error/no-warning-popup contract: PASS.

RVA1-C.16 is closed and protected.


## RVA1-C.17-B.8 / A.10-A.39 — NES System-Level Geometry — COMPLETE

Protected parent checkpoint:

`cef6d6ddc15752e9493b98e018d726fec19197b2`

A.10-A.39 closes the NES system-level presentation-geometry
validation boundary.

The human-approved A.35 NES geometry remains unchanged.

### Production geometry ownership

Read-only provenance and composition audits established that the
approved NES presentation geometry is already owned by RetroVault's
source-controlled native NES visual package:

- `RetroVault_NES_Classic.cfg`
- `RetroVault_NES_Classic.runtime.cfg`
- `RetroVault_NES_Classic.shader.cfg`

The deployed `/opt` NES package is byte-identical to the repository
package for the overlay, runtime, and shader descriptors.

Legacy external RetroArch state was not promoted into RetroVault.
The inspected Flatpak live-proof configuration only activates the
overlay, and the legacy Nestopia override predates this geometry
boundary and does not supply the approved presentation correction.

### Runtime composition contract

Production launch composition consumes the native NES geometry
automatically.

`OverlayRuntimeConfig` resolves the sibling `.runtime.cfg` descriptor
from the selected NES overlay and places its approved RetroArch
geometry controls into RetroVault's transient `--appendconfig`.

The protected NES runtime contract remains:

- `aspect_ratio_index = "22"`
- `video_force_aspect = "true"`
- `custom_viewport_x = "0"`
- `custom_viewport_y = "0"`
- `custom_viewport_width = "1920"`
- `custom_viewport_height = "1080"`

`ShaderRuntimeConfig` independently resolves the sibling
`.shader.cfg` descriptor and composes the approved shader correction
into the transient shader preset used by the production launcher.

The protected NES shader correction remains exactly:

- `HSM_NON_INTEGER_SCALE = "88.000000"`
- `HSM_SCREEN_POSITION_Y = "-3.000000"`

No additional HSM geometry controls are introduced.

### System-level invariant

The NES geometry contract belongs to the native NES presentation
package rather than to an individual ROM identity.

A durable regression now verifies that multiple unrelated NES game
identities using the same production NES overlay resolve identical
runtime geometry and identical shader correction.

This protects the intended system-level behavior against accidental
future conversion into title-specific geometry and directly covers the
random-title consistency concern that initiated this validation pass.

Per-game presentation assignment remains supported by the general RVV
architecture, but the approved NES Classic geometry itself contains no
ROM/title-specific dependency.

### A.39 validation

A.39 validation established:

- real production NES runtime-descriptor composition: PASS;
- real production NES shader-descriptor parsing: PASS;
- transient shader composition: PASS;
- system-level multi-title geometry regression: PASS;
- NES production-asset regression: 10 passed;
- production-composition regression: 74 passed;
- targeted NES / RetroArch / RVV regression: 709 passed;
- complete RetroVault regression: 1435 passed;
- Git diff integrity: PASS; and
- protected parent integrity: PASS.

No production geometry, artwork, shader values, RetroArch global
configuration, core override, or external runtime state was modified
during A.39.

### Protected result

The A.35 human-approved NES geometry is now durably protected as a
source-controlled, system-level production contract.

**RVA1-C.17-B.8 / A.10-A.39 is complete.**

## RVA1-C.17-B / A.3-L — Universal Presentation Authority Repair — COMPLETE

Protected engineering checkpoint:

`6ab5cf9c681984bb15a2d3418eb07ea1bb2ff009`

Commit:

`fix: enforce universal RetroVault presentation authority`

A.3-L supersedes the earlier NES A.10-A.39 runtime geometry values after
expanded production validation exposed launch-state inheritance,
duplicate-presentation risk, source-edge cropping, shader-side geometry,
archive-format coverage gaps, and RetroArch process-lifecycle ownership
requirements.

The historical A.10-A.39 section above remains preserved as development
history. Its 1920x1080 viewport and 88% / -3 shader correction are not
the current NES production contract.

### Universal presentation-authority architecture

RetroVault now establishes one launch-scoped presentation authority.

Production launch composition:

- clears inherited RetroArch overlay state before applying RetroVault's
  selected overlay;
- clears inherited shader state before applying RetroVault's selected
  shader;
- owns the final physical gameplay viewport through RetroVault's runtime
  descriptor;
- preserves emulator source content before final viewport composition;
- prevents the CRT shader from becoming a second scale, crop, aspect, or
  position authority;
- keeps presentation geometry system-level rather than title-specific;
  and
- owns the complete RetroArch launch process group so wrapper, sandbox,
  and emulator descendants are terminated and reaped together.

This architecture is intended to be reusable across supported RetroVault
platforms rather than implemented as per-game launch correction.

### Current NES production geometry

The protected NES runtime contract is:

- `aspect_ratio_index = "22"`
- `video_force_aspect = "true"`
- `video_aspect_ratio = "-1.000000"`
- `video_aspect_ratio_auto = "false"`
- `video_crop_overscan = "false"`
- `video_scale_integer = "false"`
- `video_viewport_bias_x = "0.500000"`
- `video_viewport_bias_y = "0.500000"`
- `custom_viewport_x = "355"`
- `custom_viewport_y = "100"`
- `custom_viewport_width = "1206"`
- `custom_viewport_height = "762"`

The fixed 1206x762 viewport matches the transparent aperture in the
RetroVault NES Classic 1920x1080 overlay.

No per-title NES geometry is permitted by this production descriptor.

### NES source preservation

FCEUmm launch-scoped core options preserve legitimate source content on
all four edges:

- `fceumm_overscan_h_left = "0"`
- `fceumm_overscan_h_right = "0"`
- `fceumm_overscan_v_top = "0"`
- `fceumm_overscan_v_bottom = "0"`

Cropping is therefore not used to force individual games into the
RetroVault aperture.

Game-authored internal positioning or black regions remain legitimate
game content and do not alter the system-level RetroVault viewport.

### Geometry-neutral CRT contract

RetroVault/RetroArch owns physical geometry.

The NES runtime shader descriptor now uses:

- `HSM_NON_INTEGER_SCALE = "100.000000"`
- `HSM_SCREEN_POSITION_Y = "0.000000"`

The persistent RetroVault NES CRT preset establishes the neutral
baseline:

- horizontal position = 0;
- vertical position = 0;
- zoom/crop = 0;
- top/bottom/left/right crop = 0; and
- non-integer scale = 100%.

The obsolete shader-side geometry compensation is not part of the
current production contract.

### Single bezel / artwork authority

The production NES package uses one RetroVault native overlay authority.

Launch-scoped session isolation prevents stale global, legacy RetroPie,
or per-game RetroArch overlay state from composing a second bezel over
the selected RetroVault presentation.

The CRT preset is screen-only treatment and does not provide a second
bezel/artwork authority.

The same single-authority contract is protected for the existing SNES
production presentation without changing the previously human-approved
SNES physical geometry.

### Archive and launch coverage

The production archive runtime now recognizes NES `.unf` / `.unif`
content in addition to the established NES content formats.

The GoodNES validation corpus established:

- physical archives: 1971;
- RetroVault-qualified archives: 1971;
- failed archives: 0;
- playable members inspected: 22094;
- `.unf` playable members recognized: 155; and
- RetroArch instances launched by the full-corpus static audit: 0.

Full-corpus validation is intentionally static. RetroVault must not
mass-launch the game corpus.

Representative live validation is bounded to a maximum of one real
emulator launch tree at a time.

### Process-lifecycle safety

Production RetroArch launches receive a dedicated process session/group.

RetroVault shutdown signals the complete owned process group and
synchronously reaps the launcher-owned process root.

Live validation established that the shell wrapper, Flatpak/bwrap
infrastructure, and actual `/app/bin/retroarch` process belong to one
owned launch tree rather than independent emulator launches.

The safety invariant for future live validation is:

**maximum one real emulator instance / one production launch tree at a
time.**

### Production validation

A.3-L established, among other protected evidence:

- complete GoodNES archive qualification: 1971 / 1971;
- representative 24-title production launcher corpus: PASS;
- Touch Down Fever transient launch anomaly not reproduced across
  subsequent controlled production launches;
- launch-scoped overlay/shader isolation: PASS;
- FCEUmm four-edge source preservation: PASS;
- canonical NES viewport authority: PASS;
- geometry-neutral CRT shader contract: PASS;
- single RetroVault overlay authority: PASS;
- `.unf` / `.unif` archive support: PASS;
- dedicated RetroArch process-group ownership: PASS;
- clean process-group termination and synchronous reap: PASS;
- bounded native RetroArch screenshot generation: PASS;
- native screenshot behavior classified as render-region capture rather
  than complete compositor canvas;
- static overlay aperture classification: exact 1206x762 transparent
  aperture at X355 Y100;
- critical A.3-L regression: 130 passed;
- full pre-closure RetroVault regression: 1484 passed;
- Python and Git integrity gates: PASS;
- protected atomic commit and push: PASS;
- local/origin synchronization: PASS;
- clean worktree: PASS; and
- final live RetroArch state: ZERO.

### Protected result

A.3-L replaces fragmented/inherited NES presentation behavior with a
launch-scoped single-authority production contract.

The repair is intentionally architectural: platform packages may supply
their own historically appropriate geometry and presentation assets, but
a game launch must not accumulate competing geometry, overlay, shader,
or inherited RetroArch authorities.

NES is the validated production proof of this contract.

Existing human-approved SNES geometry remains protected and unchanged.

**RVA1-C.17-B / A.3-L is complete and protected.**

## RVA1-C.17-B / A.4-C.8 — NES viewport live-qualified; SNES bezel repair accepted

The current requirement is platform-specific artwork with an opening that matches
correctly proportioned gameplay edge to edge. NES now opts into a movable inner
frame: its original outer housing/branding are preserved, while the opening uses
the same resolved geometry as the final RetroArch viewport. The intermediate
full-glass stretching candidate is removed. Config-layer and viewport-bias repairs
are retained, and NES/SNES CRT shaders follow RetroArch's aspect-correct viewport.
Other platforms and live mid-game aspect changes remain separate qualification
work. The user accepted the NES gameplay checks in 1943, Adventure Island,
and The Addams Family ("All check out ok!"). The SNES right-side gray-panel gap was repaired by precisely mirroring the
left panel and rim; the user visually accepted that result on 2026-09-28.

See [a4c8_viewport_qualification.md](a4c8_viewport_qualification.md) for renderer
evidence, cross-aspect tests, scope limits, and the NES gameplay acceptance.
Protected HEAD remains `a1b472317d0a4d18626eea0dc4b75d8a389c912f`.
No commit or push before live qualification passes.


## Ecosystem Milestone #1 — Architecture contracts — COMPLETE

Closed: 2026-09-28. Scope: the approved architecture-contract plan for RetroVault
and RVDB. The existing architecture is retained; no replacement architecture or
later ecosystem milestone is introduced.

Current contract reference: [Architecture contracts](architecture_contracts.md).

### Acceptance record

| Approved deliverable | Closure evidence |
| --- | --- |
| Define six boundaries and ownership | Contract documentation identifies RVDB knowledge, local inventory, persistence, presentation resolution, runtime configuration, and process execution, including their existing classes/services and permitted dependencies. |
| Preserve identities and durable formats | RVDB IDs, ROM-path keys, bundle envelope, user-store formats, and calibrated presentation assets remain unchanged. |
| Enforce producer/consumer handoff | Fresh producer source is validated before export; malformed consumer reloads retain the last valid snapshot. Existing service fallback semantics remain supported. |
| Repair library refresh consistency | Complete Game/variant metadata is refreshed while preserving surviving objects; failure restores physical inventory, visible projection, sources, and prior object state. |
| Make runtime inputs consistent | Validation, aspect probe, and execution share the configured command. Explicit primary config is isolated once; isolation failure prevents process creation. XDG-aware primary cache storage and exit cleanup are verified. |
| Preserve presentation authority | READY production-package authority, manual-resolution precedence, append-layer ordering, and existing geometry remain protected. UI warning text no longer promises that production visuals will be absent. |
| Verify contracts | Both full regression suites pass; dependency guards, malformed-input tests, refresh rollback, primary-config source preservation/cleanup, and rejected unisolated launches are covered. |
| Record exclusions and risks | Bundle drift and other retained limitations have explicit disposition below and in the current contract reference. |

### Scope disposition

No approved Milestone #1 implementation item remains open. This closure does not
assert that all ecosystem technical debt is resolved:

- Source/bundle drift: retained as an explicit exclusion. Four bundle-only entities
  and relationship differences require a separate knowledge/evidence decision.
  Neither bundle was rebuilt or published; their audited hashes are unchanged.
- Host-path portability, identity migration, mutable low-level compatibility access,
  and live mid-game aspect qualification: existing documented limitations, outside
  this milestone. They are not silently assigned to Milestone #2.
- No live emulator qualification, user-state migration, asset deployment, or changes
  to accepted visual calibration were needed for this contract milestone.

### Delivery state

Closure is recorded in the working trees. No release, commit, push, or clean-checkout
claim is implied. RetroVault also contains pre-existing uncommitted startup and
visual qualification work, including shared-file changes, which remains preserved.
Historical protected commit IDs above refer to their original checkpoints, not to
this new milestone. Milestone #2 remains unstarted pending its own instructions.


### Final verification

- RetroVault full regression: **1,864 passed**.
- RVDB full regression: **372 passed**; producer code unchanged during the final
  closure audit, with its passing full-suite result retained.
- Final targeted launcher/dependency regression: **56 passed**.
- Fresh RVDB source validation: **53 valid entities**, zero schema or relationship errors.
- Both distributed bundle hashes unchanged; hardened consumer loading passes.
- Python parsing and both repositories' diff integrity checks pass.

**Milestone #1 is closed within its approved scope.**


## Ecosystem Milestone #2 — RVDB source/bundle reconciliation — COMPLETE

Closed: 2026-09-28, within the approved plan. Milestone #1 remains closed; its
previously deferred source/bundle discrepancy is now resolved. Statements in older
milestones about deferral or Milestone #2 not having started describe their original
checkpoints, not current status. Milestone #3 has not started.

### Acceptance record

| Approved deliverable | Verified result |
| --- | --- |
| Restore canonical source ownership | Four YAML records added for MAME, Mupen64Plus-Next, and their existing Arcade/N64 compatibility claims. |
| Restore existing associations | Only frontend.retroarch, platform.arcade, and platform.nintendo.n64 gain the relationships already distributed in the bundles. |
| Preserve knowledge | All 57 node payloads equal both pre-reconciliation bundle node maps, including evidence text/dates and playability. No new universal compatibility claim is made. |
| Validate and generate | 57 valid source entities; zero schema/relationship errors; 57 nodes and 57 edge-map entries generated by the existing validated producer. |
| Synchronize artifacts | Tracked RVDB artifact and RetroVault local copy are byte-identical; only missing empty edge entries and canonical serialization change. |
| Unify consumer relationship authority | RVDBService.retroarch_view() consumes exported launches_core edges, consistent with other views; conflicting/missing representations are tested. |
| Prevent unnoticed drift | New producer regression compares a validated fresh build with the tracked artifact and tests deterministic generation. Cross-repository equality is an explicit synchronization check, not a silently skipped test. |
| Preserve downstream boundaries | IDs, schemas, user stores, library identity, runtime core mapping, visual assets, and execution are unchanged. N64 and Arcade remain UNCONFIGURED. |

### Provenance and delivery

The bundle-only additions originated in RVDB commits `0832a93` and `291ade1`.
Their evidence is preserved with its original `2026-09-23` dates. Static official
metadata corroborated identity during analysis; local runtime qualifications were
not rerun. `core.mame` remains the Libretro core identity, not a new standalone
emulator or a replacement for individual arcade hardware identities.

Current shared SHA-256:

`cbe52800852543f88bdaf033bb0d50e348ffe64368391498ff93d72a785610dc`

RVDB's generated artifact is tracked. RetroVault intentionally ignores `data/rvdb/`;
its synchronized bundle remains local runtime data. The explicit copy-and-compare
workflow is documented in RVDB's `docs/architecture.md` under "Bundle delivery and
drift prevention" and referenced from RetroVault's architecture contracts. No ignore
policy, automatic updater, packaging/deployment system, or sibling-checkout runtime
dependency was introduced.

### Verification

- Baseline suites: **1,864 RetroVault / 372 RVDB passed**.
- Final full suites: **1,869 RetroVault / 375 RVDB passed**.
- Focused checks: **102 RetroVault / 20 RVDB passed**.
- Source validation, source/artifact parity, repeat-build determinism, and explicit
  consumer-copy equality: **PASS**.
- Source delta: exactly four additions and three relationship-only updates.
- Historical evidence and all pre-reconciliation node payloads: **preserved**.
- Python parsing and both repositories' diff integrity: **PASS**.

Three older Sega production tests also required their exact frontend core lists to
include the two reconciled cores. Their checks still enforce exactly one edge for
the reused Genesis Plus GX core; no unrelated core relationship was added.

### Scope and closure

All approved Milestone #2 deliverables are complete. No live emulator launch, ROM
scan, user-state migration, visual recalibration, external asset deployment, new
platform readiness, or broader knowledge population was performed. Automatic
bundle distribution and Milestones #3–#14 remain outside this milestone.

Closure is in the working trees. Existing uncommitted Milestone #1, startup, and
calibration work remains preserved. No commit, push, release, or clean-checkout
claim is implied. The historical protected checkpoint IDs above are unchanged.


### Final acceptance audit — 2026-09-28

A fresh build through the validated production build entry point was generated in
a temporary directory and compared against a repeat build, the tracked RVDB bundle,
and RetroVault's local runtime copy. All four are byte-identical, with the shared
SHA-256 recorded above. Every one of the 57 node payloads still matches both
pre-reconciliation bundles, and all 57 exported relationship entries match source.
The live consumer read models preserve both promoted cores, their three evidence
records, and their scoped playability values. Arcade and N64 remain UNCONFIGURED
for production presentation. Both diff integrity checks pass.

No further production changes were needed. The passing full-suite results remain
1,869 RetroVault tests and 375 RVDB tests; unchanged suites were not redundantly
rerun for this documentation-only closure. No persistent bundle was regenerated by
this final audit. Remaining approved Milestone #2 work: **none**.

**Milestone #2 is fully closed within its approved scope. Milestone #3 has not started.**


## Ecosystem Milestone #3 — Game/file identity & persistence — COMPLETE

Closed: 2026-09-28, within the approved plan. The existing library, RVDB,
persistence, presentation, and execution architecture remains the foundation.

### Acceptance record

| Approved deliverable | Closure evidence |
| --- | --- |
| Durable local file identity | Versioned IdentityRegistry stores opaque IDs, current locations, platform context, fingerprints, and sticky legacy aliases. Registry remains local user data. |
| Conservative reconciliation | Unique registered moves reconnect; replacements receive new IDs; copies remain separate; ambiguous matches do not merge. Overlapping source locations deduplicate. |
| Persistence migration | LibraryState, CollectionStore, and PresentationStore read legacy formats and write version 2. Original backups, retained unresolved entries, prevalidation, atomic writes, and restart-safe retries are tested. |
| Preserve assignment conflicts | Presentation conflicts remain recoverable in legacy_games; clearing the local override cannot resurrect them. |
| Edition/family semantics | Favorites/collections project all represented editions; removal clears represented memberships; recent history projects each family once. Presentation remains edition-specific. |
| Correct selected-edition feedback | Edition records, reconstructed targets, and singleton selectors carry local IDs. Successful launch records the selected edition; archive extraction paths never become persisted identity. |
| Consistent presentation identity | Studio uses local file IDs, canonical platform IDs, and the production resolve(game) interface. Existing shader/overlay/visuals pages inherit the shared helper. |
| Preserve refresh/import guarantees | Registered refresh preserves surviving visible objects across moves. Failure restores prior sources, lists, and object fields; registered bulk import also restores its prior snapshot on failure. Durable migration checkpoints remain resumable. |
| Verify and document | Full RetroVault regression: 1,902 passed. Both bundle hashes unchanged and equal. Python parsing and both repository diff checks pass. Contract documentation specifies migration, recovery, costs, and exclusions. |

### Verification and scope

- Initial compatibility regression after updates: **1,869 passed**.
- Focused identity/migration/edition/archive/presentation regression: **90 passed**.
- Final complete RetroVault regression: **1,902 passed** (33 new cases).
- Tests used temporary ROM fixtures and isolated XDG configuration/cache locations.
- No real user-state migration, emulator launch, ROM corpus scan, or deployment was
  performed. Runtime behavior was exercised with existing test doubles.
- No RVDB producer/source changes were needed. Milestone #2's passing RVDB suite
  remains **375 tests**; the unchanged suite was not rerun for this milestone.
- Shared bundle SHA-256 remains
  `cbe52800852543f88bdaf033bb0d50e348ffe64368391498ff93d72a785610dc`.

Initial fingerprinting requires reading discovered file contents. Unchanged files
reuse fingerprints; changed stat signatures require rehashing. Move recovery starts
after registration and remains conservative in ambiguous cases. Archive-member
identity, repacked-archive equivalence, persistent family IDs, save-state relocation,
cloud sync, multi-process store coordination, RVDB expansion, visual/runtime changes,
and later milestones are explicitly outside scope. Previously invalid canonical
Studio keys remain recoverable unresolved entries; migration does not guess which
physical edition they belong to.

All approved Milestone #3 deliverables are complete. Existing uncommitted Milestone
#1/#2, startup, and visual-calibration work remains preserved. No commit, push,
release, or clean-checkout claim is implied.

**Milestone #3 is closed within its approved scope. Milestone #4 has not started.**

### Final acceptance audit — 2026-09-28

Reviewed the implemented registry/reconciliation rules, store migration ordering,
production LibraryController/PresentationStore wiring, family projection, selected
edition feedback, and UI identity consumers against the approved scope. No further
production changes were needed.

The closure regression passed **116 tests** using fresh isolated XDG locations,
covering identity, migration, edition selection, archive launch feedback,
Presentation Studio, and Systems recent counts. The full-suite result remains
**1,902 passed**; unchanged production code did not require another full run.
Both repositories' diff checks pass, and both RVDB bundle hashes remain equal to
the Milestone #2 hash above. Existing unrelated working-tree changes are preserved.

Remaining approved Milestone #3 work: **none**. Completion is recorded in the
working tree; no commit, push, deployment, or real user-state migration is implied.
Milestone #4 remains unstarted.


## Ecosystem Milestone #4 — Core selection/readiness — COMPLETE

Closed: 2026-09-28, within the approved plan. No replacement architecture was needed.

### Acceptance record

| Approved deliverable | Verified result |
| --- | --- |
| Canonical selection | CoreMapper accepts canonical platform IDs and display aliases; scanner prefers resolved IDs. Display-name changes do not lose the mapped core. |
| Deterministic resolution | Exact normalized identity, stable ordering, explicit-path validation, symlink alias deduplication, structured ambiguity/missing/unusable outcomes. No first-match fallback. |
| Policy enforcement | Sole local defaults retained; multiple candidates require selection; incompatible explicit requests fail. Existing mappings and qualification states unchanged. |
| Usable prerequisites | Executable/PATH checks, readable nonempty native core/content checks, optional canonical compatibility, and specific reasons. Core libraries do not need executable permission. |
| UI integration | Game Details consumes structured results, reloads core-directory settings, handles settings errors, and preserves selected-edition identity and the active launcher command. |
| Launcher enforcement | Common prerequisites run for direct callers before archive/config preparation or process creation. Existing canonical production-package gates remain enforced. |
| Settings consistency | Core-directory validation reuses file eligibility rules; it does not claim game or production readiness. |
| Preservation | RVDB source/bundles, durable identities/stores, runtime composition, process ownership, production assets, and UNCONFIGURED states retained. |
| Verification | Full suite: 1,933 passed (31 new cases); Python parsing, bundle parity, and both diff checks pass. |

### Validation and delivery

The new cases exercise actual temporary filesystem fixtures and mock process
creation. Existing composition/lifecycle tests isolate filesystem prerequisites;
existing UI tests use structured resolver doubles rather than host-installed cores.
The full regression includes the identity/persistence protections from Milestone #3.
No live emulator launch, user ROM scan, real user-state migration, core deployment,
RVDB rebuild, or asset modification was performed for Milestone #4.

Both bundles retain SHA-256
`cbe52800852543f88bdaf033bb0d50e348ffe64368391498ff93d72a785610dc`.
The unchanged RVDB producer retains its Milestone #2 full-suite result of 375 passing
tests; that suite was not redundantly rerun for application-only work.

Core installation/updating, persistent core-preference UI, automatic alternate-core
fallback, firmware and ABI verification, cross-platform deployment, new compatibility
claims, READY promotions, live gameplay qualification, save migration, and later
milestones remain outside scope. File prerequisites alone do not prove emulation or
production readiness; the package gate and execution result remain separate.

Remaining approved Milestone #4 work: **none**. Changes remain in the working tree,
alongside preserved prior milestone/startup/calibration work. No commit, push,
release, or clean-checkout claim is implied.

**Milestone #4 is complete within its approved scope. Milestone #5 has not started.**

### Final acceptance audit — 2026-09-28

Rechecked canonical selection, exact binary resolution, ambiguity handling,
filesystem prerequisites, fresh core-directory settings, direct-launch enforcement,
and production-package gates against the approved Milestone #4 scope. No further
production changes were needed.

The final closure regression passed **246 tests** with fresh isolated XDG locations,
covering core selection/resolution, validation, Game Details status/lifecycle,
launcher/process ownership, production readiness, and Settings. The full-suite
result remains **1,933 passed**; unchanged production code did not require another
full run. Both repositories' diff integrity checks pass. Compatibility policy and
LaunchProfile have no milestone changes, and both RVDB bundles retain the matching
Milestone #2 SHA-256 recorded above.

Remaining approved Milestone #4 work: **none**. The completion is recorded in the
working tree. No commit, push, deployment, real user-state migration, or live
emulator qualification is implied. Milestone #5 remains unstarted.
