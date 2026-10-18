# USQE Milestone #9 — First complete platform expansion batch

Status: **COMPLETE within the bounded Master System qualification below.**

Earlier sections are chronological checkpoints; pending statements describe their
then-current state. The final acceptance section supersedes those pending items.

The user approved continuation of the bounded Master System plan. Starting
checkpoints: RetroVault `55d2197e4ebe22138a3ae33ff9b70d7f968805d8`;
RVDB `cc7b5e919f337910601738018b99c05007879c47`.
No Milestone #10 work or publication is authorized by this record.

## Approved scope and protected boundaries

Master System first, using the installed Genesis Plus GX core and existing
Library, persistence, presentation, runtime, process-ownership and recovery
architecture. Its own package design requires user approval before production
deployment. Keep NES/SNES/Genesis assets, geometry, policies, user data and RVDB
schemas/IDs unchanged. No real save migration, archive expansion, physical-gamepad
certification, new backend or live geometry-switching mechanism.

SG-1000 remains conditional and is not included in implementation. Its `.sg`
extension also identifies SC-3000; the existing resolver correctly declines to
guess. No ambiguous-extension contract is changed to fill the batch.

## Verified starting facts

- RVDB already contains Master System identity, `.sms`, shared-core relationship
  and evidence-backed compatibility knowledge. These are not local readiness.
- The configured core resolver finds Genesis Plus GX for Master System.
- Master System remains UNCONFIGURED, with no canonical production package.
- SavePolicy and save-context extension checks originally excluded `.sms`.
- No `.sms` files were found under `/home/oilcan/roms` during the initial inventory.
  The user's selected fixture location remains pending.

## Implemented preparation

The existing SavePolicy and save-context services now accept loose `.sms` files.
No storage is created merely by inspecting an edition; isolation remains opt-in.
No production launch gate or selection policy has changed.

Regression-first result: **1 failed, 2 passed** before the extension change.
Focused result afterward: **29 passed**, including controlled same-target state
backup/restore, separation from another edition, disabling without deleting saves,
unconfigured package rejection and ambiguous `.sg` identification.
These synthetic fixtures are never executed and do not establish real emulator
save compatibility. Evidence: `build/usqe9/save-preparation-before.log` and
`build/usqe9/save-preparation-after.log`.

## Remaining implementation and evidence

1. Obtain user-selected loose Master System fixtures and record hashes.
2. Prepare and review a distinct Master System package design with established
   RetroVault branding conventions; do not reuse Genesis artwork as its identity.
3. Validate package/aperture, core-reported aspect, input and configuration layers
   using controlled qualification before production activation.
4. Extend existing pipeline/save runners for the selected platform.
5. Verify import/refresh/restart, actual gameplay input, state recovery and an
   in-game save where supported by the selected cartridge. Record non-applicable
   save categories honestly.
6. Complete full regressions, RVDB validation/parity, protected checksums and
   targeted human acceptance, then update current documentation for closure.

No new package, fixture, controller behavior or live result is accepted yet.

Preparation checkpoint: full RetroVault suite **2,451 passed** in isolated XDG
locations with Qt offscreen (`build/usqe9/full-suite-preparation.log`). All 47
protected checksums from the preceding milestone still match. Git whitespace
checks passed. No commit, push or live emulator run was performed.

## Presentation concept review

A first review-only concept is saved at
`design/master-system-model1/Master_System_Model1_concept_v1.png`, with the exact
built-in image-generation prompt and limitations in the adjacent README. It has
not been deployed or entered in the production catalog. The user must review the
appearance; generated opening dimensions are not calibrated production geometry.
Master System game fixtures and live acceptance remain pending.


## Appearance selection — 2026-10-18

The user approved the original Master System concept v1: “Let's stick with the
top one, your original sega master system bezel looks great!”
Selected source: `design/master-system-model1/Master_System_Model1_concept_v1.png`.
Version 2 remains an unused alternative. Preserve v1's RetroVault wordmark with
double gold rules and Sega Master System® branding during package preparation.
This approves appearance only; package geometry, deployment, real gameplay and
save qualification remain pending. Master System is still UNCONFIGURED.

## User-authorized source layout update — 2026-10-18

The Starter Suite parent remains `/home/oilcan/roms/Starter Suite Roms`.
Current sources are `Nintendo/Nes`, `Nintendo/Snes`, `Sega/Genesis` and
`Sega/Master System`. With explicit user authorization, the nine existing loose
ROMs were moved from the three old folders and verified byte-for-byte by SHA-256.
Old folders were retained, with no overwrite. The original three source IDs were
preserved; Master System received its own source. Overlapping recursive parent
sources were disabled; separate archive sources were preserved.

This is an explicit user-requested runtime source configuration change, not a
milestone migration of Library identities, saves, preferences or history. The
previous runtime configuration and move hashes are retained locally under
`build/source-layout-update/`. Historical qualification paths remain historical;
future qualification must use the new paths. Library refresh has not been invoked
by this operation. Master System's new folder is still empty.

The user subsequently authorized removing the old folders after completion.
All nine destination checksums were reverified, and only the three empty legacy
directories were removed with `rmdir`. The four new system folders remain intact.

## Fixtures available — 2026-10-18

The user supplied two loose Master System games in the new source folder:

| Fixture | Bytes | SHA-256 |
| --- | ---: | --- |
| Golden Axe Warrior (USA, Europe, Brazil) (En).sms | 262144 | `164223b3c2e0e081f7908a6a6828b23f0e75934f215e98b1094958bb96ec51a4` |
| Road Rash (Europe, Brazil) (En).sms | 524288 | `46d01d61fb8d4e039762a7088ebca27483a1a7b1b33b5907d42f0b624d86e301` |

Both completed the existing full-window headless aspect probe using disposable
copies, isolated core options/configuration/save output, and the installed
Genesis Plus GX binary. Both reported aspect 1.524. Owned processes were reaped
and probe temporary files removed; original ROM hashes and primary config were
preserved. This is startup evidence only, not visual/input/save acceptance.
Evidence: `build/usqe9/master-system-fixtures-20261018/report.json`.

The approved concept is RGBA at 1672×941. Pixel inspection found faint alpha=1
residue inside its otherwise transparent gameplay opening. A built-in image-tool
cleanup attempt is retained as `design/master-system-model1/Master_System_alpha_candidate.png`;
it also contains alpha=1 residue and is not accepted for deployment. The approved
v1 remains the design authority. A precise rectangular alpha cutout is needed;
no production package or readiness was activated.

## Deterministic alpha cutout

The user explicitly authorized scripted image editing for the aperture cleanup.
`tools/prepare_master_system_artwork.py` creates a separate native-resolution
candidate from approved v1. Bounds `(274,72)` through exclusive `(1398,736)`
are inside the existing beveled opening. All alpha values within that rectangle
are zero. Every pixel outside it, and all RGB values throughout, are unchanged.
The original source is preserved. Verification is recorded in
`design/master-system-model1/Master_System_Model1_runtime_cutout.json`.

The candidate remains 1672×941; this is not a claim of calibrated 1920×1080
runtime geometry. Package composition/display mapping and live qualification
remain to be completed. No readiness policy or existing production asset changed.

## Production package implementation and first live run

The user authorized completing production geometry, live qualification, and then
commit/push after acceptance. A dedicated Master System package is installed;
its existing policy state is READY for controlled qualification, not a completed
human-acceptance claim. The native approved cutout is displayed full-screen;
inward rounding maps its transparent opening to `(315,83,1290,761)` on the
1920×1080 qualification canvas. No gameplay image is resized by artwork tooling.
Core aspect 1.524 produces a contained viewport `(380,83,1160,761)`.

Expansion exposed two actual integration requirements: `.sms` needed adding to
the Library scanner's supported file list; and explicit platform/core policy
resolution needed to validate core membership in the selected platform policy
instead of comparing the first shared-core match by object identity. Legacy
core-only lookup and its compatibility snapshot retain Genesis's original
behavior. Separate Master System options preserve borders with overscan disabled.
Existing Genesis policy and package files remain unchanged.

The existing pipeline matrix now includes `.sms`, mixed four-platform identity
isolation, fresh-process persistence, failure stages and protection of other
platform packages. Unqualified CRT customization remains rejected for Master
System; no controls were added to its customization UI.

Golden Axe Warrior completed its first 30-second production pipeline with matching
runtime geometry, unchanged package hashes and pending human visual/input
acceptance. Evidence: `build/usqe9/golden-axe-presentation-20261018/`.
RVDB full suite: **407 passed**; source validation succeeded. Neither was modified.
The protected package/core/bundle subset from #8 (39 files) still matches. The old
user identity-store checksum no longer matches; source paths were intentionally
changed and the Library may have refreshed since then. No cause is inferred from
the checksum alone, and no rollback of user state was attempted. Current user
JSON checksums were captured before live testing in
`build/usqe9/pre-live-user-state.json`; individual isolated live runs also enforce
preservation of their actual starting user state.

Automated integration checkpoint: **2,473 RetroVault tests passed** after adding
Master System to the complete pipeline matrix. Unqualified Master System CRT
tuning is explicitly tested as a rejected request with preserved user state.
Compile and whitespace checks passed. Golden Axe Warrior human response:
“Picture and controls worked; I did not test Enter”. Presentation acceptance and
action/direction input are recorded; Start/pause remains pending. An isolated
user-paced in-game save and save-state create session was opened. Fresh-process
reload, Road Rash's representative run, final closure and authorized publication
remain outstanding; no commit/push has occurred.

## Golden Axe Warrior save/input acceptance

The first create attempt omitted F2; its failed report is retained separately.
The repeat captured both SRAM and a nonempty save state and exited cleanly.
The user identified a dead-end location surrounded by green trees as the state
checkpoint. A separate process reopened the fixture and verified persisted file
hashes before launch. Asked to test normal load/continue before F4, restore the
checkpoint with F4, test Enter pause/resume, and quit, the user replied:
“Works, *Exactly*”. Those three acceptance results are recorded in
`build/usqe9/golden-axe-save-roundtrip-20261018/reload-user-observation.json`.
Both accepted create/reload reports succeeded, retained physical identity, left
no owned process, and preserved protected user state. This is same-fixture,
same-core recovery, not cross-core save-state portability.

Two fresh RVDB builds matched each other, the canonical bundle and RetroVault's
installed bundle byte-for-byte. SHA-256:
`4d99f2b1bff694f26ca1b1ff68b7d4d1816236abb1e64d10a62e14bf20e3eb43`.
Road Rash's representative visual/input run is the remaining live acceptance.


## Final acceptance and closure — 2026-10-18

The user confirmed Road Rash with “All works 100%” after the 30-second run and
its explicit picture, bezel, arrow/X/Z and Enter pause/resume checks. Together
with Golden Axe Warrior, both presentation cases pass the existing evidence
assessment. Golden Axe Warrior additionally passed same-core in-game save and
F2/F4 state recovery across separate processes, including the green-tree checkpoint.
Road Rash save recovery is not claimed. Both production pipeline runs passed
Library import, selection, persisted preferences/history, fresh-process reconstruction,
Stop/shutdown and protected-user-file checks. No unexpected user files were created.
Temporary runtime configuration was cleaned by the existing lifecycle architecture.

Qualification is limited to the two hashed loose `.sms` fixtures above, the installed
Genesis Plus GX SHA-256
`24111ce0a24ad2c7ad5474ec208025c342d91fd243f0b74b2a9125d911a39ac1`,
RetroArch 1.22.2 (Git 69a4f0ea1e), and the single 1920×1080 scale-1 Wayland display.
Both report aspect 1.524 and actual viewport `(380,83,1160,761)` contained inside
the approved aperture `(315,83,1290,761)`. User acceptance establishes upright,
uncropped, naturally proportioned gameplay and correct bezel fit for these cases.
The package qualification metadata is finalized after acceptance; artwork, shader,
runtime directives and geometry are identical to those exercised live. Original
as-tested package hashes remain in the local qualification reports.

Final verification: **2,473 RetroVault tests passed; 407 RVDB tests passed**.
RVDB validation: **59 valid entities, zero schema/relationship errors**. Two fresh
builds, canonical bundle and installed bundle are byte-identical, SHA-256
`4d99f2b1bff694f26ca1b1ff68b7d4d1816236abb1e64d10a62e14bf20e3eb43`.
After metadata finalization, all five Master System package/save checks passed again.
Compilation and Git whitespace checks passed. The 39 protected prior package,
core and bundle files retain their Milestone #8 hashes. RVDB has no source changes.

The explicitly authorized source-folder move/configuration update is the only
intentional real-user-data operation in this milestone. No save migration or
identity rewrite was performed. The older identity-store checksum discrepancy
is documented above without attributing a cause; live qualification preserved
its own starting user state. NES/SNES/Genesis artwork, shaders and calibrated
geometry remain unchanged. Shared-core lookup preserves their existing behavior.

Remaining limitations: no physical gamepad certification, other display/layout
qualification, archive expansion, cross-core state portability, live aspect switching,
or new Master System CRT customization. SG-1000 and SC-3000 remain unconfigured;
no ambiguous `.sg` guessing was added. This batch contains one platform and stays
within the approved two-platform cap. No further platform readiness is implied.

The user authorized normal commit/push of this accepted work. The publication
commit contains this record and the tested implementation; its exact hash is
reported after remote verification. The original roadmap and earlier milestone
records remain protected. **USQE #9 is complete; #10–#12 remain unstarted.**
