# RetroVault Current Milestone

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
