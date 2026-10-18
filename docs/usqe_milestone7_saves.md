# USQE Milestone #7 — Saves and recovery

Status: **COMPLETE within the approved bounded scope.** All required live
recovery categories and the save-management screen are accepted. No additional
NES/Genesis in-game-save category was deferred. Closure is recorded in the working
tree; no commit or push has been performed. USQE #8 has not started. Original
roadmap records remain protected.

## Approved scope and boundaries

Reuse registered physical-file identity, backend selection, the shared owned
emulator session, existing launch preparation and transient configuration.
Separate SRAM/in-game saves, emulator states and configuration files. Preserve
existing saves; no automatic relocation, conversion, cross-core or cross-backend
sharing. The first implementation is bounded to registered loose cartridge files.
Archive save management remains outside this first slice; archive launches retain
existing routing. No cloud synchronization or blanket compatibility claim.

## Actual destination investigation

The installed RetroArch 1.22.2/Snes9x core was exercised using two disposable copies
of Super Mario Kart (USA), with identical basenames in different folders. These
are controlled physical-path fixtures, not claims of two distinct commercial ROM
editions. ROM SHA-256:
`2ada8919688087be60a6a48cace8f877add60c45d2e5d09e2442faa55be62a49`.
Core SHA-256:
`8b9de467659513b29821df7d34ccaa26f30834fc66f4a7b12c481f51421f0d13`.

The primary naming flags retained core sorting and disabled content-directory
sorting. Both copies wrote `saves/Snes9x/Super Mario Kart (USA).srm` in an isolated
root. A different ROM directory alone therefore does not isolate those saves.
Evidence: `build/usqe7/save-path-stop-verified-20261015/report.json`.

After explicit per-edition opt-in, production SavePolicy and transient session
configuration routed the copies to different directories. The second run left
the first copy's SRAM byte-for-byte unchanged. Evidence:
`build/usqe7/save-path-isolation-verified-20261015/report.json`.
Both runs passed ROM/core/primary-config and production core-options checksum
preservation checks. These probes verified controlled Stop and SRAM flush logs,
not normal user Quit or recovered gameplay. The Flatpak wrapper returned SIGTERM
(-15), while core unload and successful SRAM flush were independently verified;
a signal return by itself is never accepted as a pass.

Earlier exploratory probes could not use max-frames/private stdin Quit reliably
with this Flatpak/headless setup. They are not normal-Quit evidence. An early log
mentioned the production core-options destination; the file's modification/change
timestamps predated those probes. No initial before-hash was available for that
file. Subsequent probes isolated both options authorities and checked all 18
production `.opt` files before/after, with no differences.

## Implementation

- `services/saves/policy.py`: explicit per-edition/per-core RetroArch storage.
  No policy means unchanged legacy routing. Enabling starts separate storage only
  after the UI warning; disabling returns to existing routing without deleting,
  copying or merging either save set. Moving a ROM preserves its registered-ID
  destination; a basename change fails clearly rather than silently losing saves.
- `models/launch_profile.py` and `controllers/game_launch_controller.py` carry
  selected physical identity and original content path to runtime preparation.
  Temporary extraction paths never become save identities.
- `services/retroarch/launcher.py` and `session_config.py` apply approved save keys
  to transient configuration. Save directives cannot supply presentation keys.
  Permanent RetroArch configuration and normal non-opted-in routing are unchanged.
- `services/saves/context.py`: read-only selected-edition/backend destination
  resolution. Native Snes9x keeps its existing identity-derived directories.
  Unknown legacy RetroArch destinations are not guessed or offered for restore.
- `services/saves/recovery.py`: explicit backups and matching-target restore,
  with a completed safety backup before replacement, flushed atomic publication,
  failure preservation, and temporary-file cleanup. Symlink targets are rejected.
  Backup contracts bind physical identity, backend/core, content hash, runtime
  binary hash, kind and exact destination. For RetroArch the recorded runtime
  binary is the core; this does not establish frontend-version portability.
  Restore currently requires an existing selected save file; missing-save import
  and legacy-save migration are not claimed as implemented.
- `services/emulators/session.py`: file operations use the same lock as launch
  and Stop; either owned backend running blocks writes. Process ownership and
  termination safeguards are unchanged.
- `ui/library/widgets/save_manager.py` and Game Details expose destination
  inspection, explicit opt-in/revert, separate save kinds, backup and confirmed
  restore. State screenshot sidecars and configuration files are excluded.

## Verification evidence

- Destination/collision probe: passed; isolated edition routing: passed.
- Focused service/controller/runtime checks: 162 passed before round-trip runner
  tests; final verification counts are recorded below when available.
- Full regression checkpoint: **2,394 passed** before the final runner tests and
  save-directive guard additions (`build/usqe7/full-suite-final.log`).
- Tests cover edition/core separation, moves versus renames, unchanged defaults,
  enable/cancel/revert behavior, owned-session exclusion, mismatched backup
  rejection, safety backup rollback, flush/replacement failure preservation and
  temporary-file cleanup. UI tests run offscreen with isolated data roots.
- An initial broader run aborted because Qt offscreen mode was omitted. The
  corrected isolated/offscreen run passed. A later full run found one unbounded
  Mock inventing the new profile attributes; the fixture now explicitly declares
  them. Production validation was not weakened to accommodate the mock.
- No actual user save or configuration was migrated. RVDB remains unchanged.
  Assets, shaders, logos, calibrated geometry and readiness/core-selection policy
  remain unchanged. Existing M6 changes are preserved separately in the worktree.

## Current acceptance status

| Route | In-game record after fresh restart | Save-state recovery | Normal exit / cleanup |
| --- | --- | --- | --- |
| RetroArch Snes9x | Accepted: Mario Circuit 1, 1:25.20, checked without F4 | Accepted: F4 restored prior slot 0 | Passed, exit 0; no owned process |
| Native Snes9x | Accepted: Mario Circuit 1, 1:23.97, checked before F1 | Accepted: F1 restored saved screen | Passed, exit 0; no owned process |
| NES — Kirby’s Adventure | Accepted: File 1 retained door #2 before F4 | Accepted: F4 restored saved screen | Passed, exit 0; no owned process |
| Genesis Plus GX — Ghouls ’n Ghosts | Not qualified: this run was save-state only | Accepted: F4 restored level 1 orange-ladder location | Passed, exit 0; no owned process |

The native acceptance quote was “yes confirmed”, answering the two separate
checks. Both routes used separate isolated save storage. Protected-file checks
passed. No cross-backend save sharing or state-format compatibility is claimed.

Remaining approved milestone work: **none**. The user accepted the screen with
“Screen is acceptable. Continue”, retained the additional in-game-save category,
and accepted Kirby’s Adventure recovery with “Yes, all works”. The additional
Genesis state-only check supplements that required NES result; it does not replace
it. No commit/push is authorized by this record.

The user-paced runner `scripts/qualify_save_roundtrip.py` prepares isolated
configuration/state/cache/data and a ROM copy, then runs create and reload as
separate commands. It allows 15 minutes by default, requires normal successful
exit, verifies files survived into a fresh application process and records
acceptance as pending. A timeout forces owned-process cleanup and fails the
normal-Quit check. File presence is never equivalent to recovered gameplay.
Prepared RetroArch fixture:
`build/usqe7/mario-kart-retroarch-roundtrip-20261016/fixture.json`.
RetroArch in-game and save-state recovery are accepted; see the current table above.
Native fixture prepared separately at
`build/usqe7/mario-kart-native-roundtrip-20261016/fixture.json`; both recovery checks are accepted.

## Latest automated checkpoint — 2026-10-16

Full regression: **2,400 passed** (`build/usqe7/full-suite-closure-check.log`).
Focused service/controller/runtime/runner checks: **167 passed** before the final
one-case directive guard; that guard is included in the full suite. Compile/import
checks and `git diff --check` pass. Canonical and installed RVDB bundle SHA-256
remain equal: `4d99f2b1bff694f26ca1b1ff68b7d4d1816236abb1e64d10a62e14bf20e3eb43`.
RVDB worktree remains clean. These automated results do not close the pending
real save/reload acceptance categories.

## Live acceptance update — pending user observations

The first RetroArch create run exited normally (157.765 seconds, exit 0). The
user reported `1'33"34` and an F2 slot-0 save notification, then clarified that
the time came from a one-player race rather than a Time Trial. It is therefore
not accepted as an in-game saved Time Trial record. F4 was explicitly not tested
in the subsequent repeat. Earlier create/reload evidence was archived under
unique filenames; saves were retained.

The latest create repeat reached 900.021 seconds and required forced cleanup.
Its report is unsuccessful for normal-Quit qualification. It records no remaining
owned process and unchanged protected files. The log also contains a D-Bus
assertion; causality is not established. This run does not qualify save recovery.
User observations, a successful Time Trial round trip, native Snes9x acceptance
and an additional save-capable NES/Genesis fixture remain outstanding.

### RetroArch save-state recovery accepted

The user confirmed F4 restored the earlier saved screen with “yes”. Evidence:
`build/usqe7/mario-kart-retroarch-roundtrip-20261016/state-recovery-repeat-20261016T231338399060Z.json`.
The run exited normally (exit 0), left no owned process and preserved protected
files. The original slot-0 bytes were verified before launch. This accepts only
the same-core RetroArch save-state round trip; in-game Time Trial persistence
and native Snes9x recovery remain pending.

### RetroArch in-game save recovery accepted

The user reported a new Time Trial time of **1:25.20** and, after a fresh
process restart without F4, confirmed it was present on **Mushroom Cup — Mario
Circuit 1** (“Yes. Mushroom Cup Mario Circuit 1”). Both create and reload reports
record normal exit 0, no remaining owned process and unchanged protected files.
Evidence: `build/usqe7/mario-kart-retroarch-roundtrip-20261016/create.json`,
`reload.json` and `user-observations.json`. RetroArch in-game SRAM and same-core
save-state recovery are now separately accepted. Native Snes9x and the additional
NES/Genesis fixture remain pending; Milestone #7 is not closed.

### Native Snes9x recovery accepted

The user reported **1:23.97**, confirmed the Shift+F1 save notification, and then
confirmed both the Mario Circuit 1 record before F1 and the restored screen after
F1 with “yes confirmed”. The accepted repeat exited normally (exit 0), left no
owned process and preserved protected files. Evidence:
`build/usqe7/mario-kart-native-roundtrip-20261016/create.json`, `reload.json` and
`user-observations.json`. Prior repeat evidence remains archived with unique names.
This completes the two SNES backend acceptance categories, not the entire milestone.

### Genesis save-state recovery accepted — 2026-10-17

User-selected ROM: `Ghouls'n Ghosts (Japan, USA) (En,Ja).md`, SHA-256
`907ced1554c9a57eb20691706e53d7d022e47648f25936d236134623b00b90d6`.
Its backup-RAM header descriptor is blank. The isolated run produced a state file
and screenshot, not an SRAM file. No in-game save capability is inferred.

The user saved on level 1 after defeating several enemies, by an orange ladder
with a bird descending from above, and confirmed the F2 save notification. After
normal Quit and a fresh process, the user confirmed F4 recovery: “Yes it correctly
loaded the saved state”. Both runs exited 0, preserved protected files and left
no owned process. Evidence:
`build/usqe7/ghouls-genesis-state-roundtrip-20261017/create.json`, `reload.json`
and `user-observations.json`. Generated launch configuration paths were removed.

The qualification runner now supports the selected existing Genesis platform
and explicitly labels state-only coverage. It rejects state screenshot sidecars
as save evidence; the original SNES in-game-save requirements remain the default.
No platform readiness, core-selection policy or production presentation changed.

Actual themed save-manager review image:
`build/usqe7/save-manager-review-20261017.png`. It shows the one real Genesis state,
excludes its screenshot, and presents separate destinations and explicit
backup/restore/routing actions. The user accepted this screen with
“Screen is acceptable. Continue”.

Final automated checkpoint after Genesis runner coverage: **2,402 passed**
(`build/usqe7/full-suite-final-20261017.log`). Both bundle copies remain byte-equal;
`git diff --check` passes, and RVDB remains clean. No commit or push was performed.

### Additional in-game-save fixture selected — 2026-10-17

The user chose to retain the additional NES/Genesis in-game-save requirement.
Read-only inventory of the supplied parent folder identified
`Nintendo Entertainment System/Kirby's Adventure (USA) (Rev 1).nes`.
The ROM has a valid iNES signature and its battery-backed-RAM flag is set.
SHA-256: `34afcebaf04d57a42c2436fb95b933c7841e1621f1dc3be482380baef33ec3d8`.
Nintendo's original manual confirms automatic progress saving (not lives,
ability, score or vitality):
https://www.nintendo.co.jp/clv/manuals/en/pdf/CLV-P-NAAPE.pdf

An isolated copy was prepared in `build/usqe7/kirby-nes-roundtrip-20261017`.
Create/restart gameplay acceptance is pending; no deferral is being taken.
The previously accepted SNES and Genesis results remain preserved.

## Final closure evidence — 2026-10-17

Kirby’s Adventure create/reload completed through the existing NES launch route.
The user reached door #2, quit normally, then confirmed File 1 retained that
progress before F4 and that F4 restored the saved screen: “Yes, all works”.
Evidence: `build/usqe7/kirby-nes-roundtrip-20261017/create.json`, `reload.json`
and `user-observations.json`. This satisfies the retained additional NES/Genesis
in-game-save requirement; no coverage deferral was needed.

Final complete suite: **2,402 passed**. Only documentation/evidence recording
changed after that run. Final protected-file checksum and generated-launch-file
checks passed for all four live fixtures. All accepted reloads exited 0 with no
owned process remaining. Failed/timed-out attempts remain historical evidence,
not acceptance. The user accepted the actual themed save-management screen.

The observed baseline basename collision is corrected by explicit opt-in
physical-edition/core routing. Separate copied-content probes verified that one
edition’s run leaves the other’s save untouched. Existing default routing and
native identity-derived directories remain intact. Backup/restore failure,
rollback and ownership guards passed controlled tests. Legacy-save migration,
archive save management, missing-file import, cross-core/backend conversion,
cloud synchronization and universal version portability remain outside this
bounded implementation; they are not silently claimed as delivered.

No production assets, calibrated geometry, shaders, platform readiness, core
selection, RVDB source/schema/canonical IDs or real user save/configuration data
were changed by Milestone #7. Earlier M6 changes remain preserved in the same
working tree. Canonical and installed RVDB bundle SHA-256 remains
`4d99f2b1bff694f26ca1b1ff68b7d4d1816236abb1e64d10a62e14bf20e3eb43`.
RVDB remains clean. `git diff --check` passes. Publication is not claimed.

**USQE Milestone #7 is complete; Milestones #8–#12 remain unstarted.**
