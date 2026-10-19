# USQE Milestone #10 — Sustained-session and recovery qualification

Status: **COMPLETE within the recorded bounded scope.**
#11–#12 remain unstarted. Earlier sections are chronological checkpoints; the final
verification below supersedes their pending items.
Starting checkpoints: RetroVault `b3efab258e78b6fbc76d2eaa2768a37a235bf0e6`;
RVDB `cc7b5e919f337910601738018b99c05007879c47`.

The user approved five ten-minute representative sessions. Existing runtime runners
now accept an explicit sustained mode requiring exactly 600 seconds; ordinary
smoke runs retain their 1–30 second limits. RetroArch sustained mode requires the
isolated Library pipeline. No production policy or assets changed.
Regression: **2,484 tests passed**. New mode validation covers nonfinite/bool and
out-of-bounds values, explicit opt-in, pipeline restriction and pending human
acceptance. These are not universal endurance or memory-leak guarantees.

## Live evidence — 2026-10-19

| Route / fixture | Seconds | Automated result | Human gameplay |
| --- | ---: | --- | --- |
| NES / Kirby's Adventure | 600.065 | Pass | Accepted |
| SNES RetroArch / Super Mario Kart | 600.083 | Cleanup failed; other stages passed | Accepted |
| Native Snes9x / Super Mario Kart | 600.097 | Pass, including 3.004-second fresh-process restart | Accepted |
| Genesis / Sonic the Hedgehog | 600.072 | Pass | Accepted |
| Master System / Golden Axe Warrior | 600.002 | Pass | Accepted |

Evidence is retained under `build/usqe10/*-sustained-20261019/`, including the
original reports and separate human-acceptance records. The user confirmed NES
with “Yes, all checks passed”, SNES/native/Genesis with “Everything stayed correct.”,
and finally “I confirm *ALL* are correct.” These establish observed controls,
picture and audio continuity; they do not override automated cleanup failures or
prove new save-recovery outcomes. All runs preserved their protected user files.

## Open cleanup finding

SNES left `cache/retrovault/primary-runtime/retroarch_qt.cfg` inside its isolated
runtime root. Its content is desktop-menu preferences. There was no remaining
owned process. The transient source enables the desktop menu and binds it to F5;
there is no evidence establishing which event triggered the file's creation.
`PrimaryConfigRuntime.create()` writes a primary file in a shared runtime directory;
`cleanup()` removes registered primary files, not emulator-created siblings.
The original failed report and file are retained. Do not delete historical caches
or relabel this run as an automated pass.

Proposed bounded repair, pending approval: give each new primary configuration a
private owned directory and clean that directory only after process ownership has
ended. Preserve unrelated files, older cache directories, source configuration,
input mappings and production presentation. Add regression coverage for sidecar
cleanup, failed/retried cleanup and preservation of unrelated directories. Verify
through controlled tests before deciding whether another live run is necessary.

## Remaining qualification

Resolve the cleanup finding; finish controlled lifecycle/recovery/repeated-session
checks and fresh save/reload acceptance for the selected save cases. Prior #7/#9
recovery evidence remains historical and is not claimed as a new #10 round trip.
Recheck bundle parity, protected assets, compilation and diff integrity; finalize
bounded documentation only after all required evidence is complete. No commit or
push has occurred for #10. No #11 work has begun.

## Approved cleanup repair and controlled verification — 2026-10-19

The user approved the bounded repair. Two regression tests reproduced the original
shared-directory/sidecar cleanup gap before implementation. `PrimaryConfigRuntime`
now registers a private directory before creating each primary file. Cleanup
removes only registered directories and preserves failed entries for retry. Older
cache contents are not discovered or deleted. The launcher retains its existing
owned-process guard before cleanup.

Verification: **2,488 full-suite tests passed** after the repair. An additional
real-child regression then passed in the **38-test focused run**: three successive
owned child sessions wrote the same kind of sidecar, cleanup was blocked while
the child was alive, and Stop reaped the child and removed its session directory
on every cycle. Additional cases cover creation failure, cleanup retry, unrelated
files and sidecar symlinks without following their targets. This is controlled
repair evidence, not a rewritten result for the original SNES live run.

All five live gameplay acceptances are recorded. Master System completed 600.002
seconds and passed automation. All 39 protected earlier package/core/bundle files
remain unchanged; canonical/installed bundle parity retains SHA-256
`4d99f2b1bff694f26ca1b1ff68b7d4d1816236abb1e64d10a62e14bf20e3eb43`.
Compilation and diff checks pass. Fresh #10 save/reload acceptance remains pending;
no milestone closure, commit or push is claimed.

## Fresh save/recovery acceptance — 2026-10-19

- RetroArch / Super Mario Kart: Mushroom Cup, Mario Circuit 1, **1:23.23**.
  User confirmed the in-game record before F4 and the separately restored state:
  “Both results return with: 1'23\"23”. Both phases exited 0, no owned process
  remained, protected files were unchanged, and the runtime cache contains no files.
- Native Snes9x / Super Mario Kart: Choco Island 1, **1:32.24**. User screenshots
  show the persisted record before F1 and restored lap-results screen afterward.
  Both phases passed, exited 0, and preserved protected files. Native session logs
  and an event-sound cache remain as retained backend output; they are not transient
  primary/control configuration or evidence of a running process.
- Master System / Golden Axe Warrior: first attempt passed F4 purple-room state
  recovery but **failed in-game recovery**. A nonempty SRAM file alone had not
  established a real saved game. This result is retained, not converted to pass.
  The manual's Sage -> Yes -> slot procedure and Button 2 confirmation were then
  explained. A fresh isolated attempt explicitly saved to File 1. The user loaded
  File 1 before F4, checked the separate state, and confirmed “Yes. Everything *Did*
  work”. Both phases exited 0, no process remained, protected files were unchanged,
  and the runtime cache contains no files.

Manual reference: https://patpend.net/manuals/sms/golden_axe_warrior.html
(transcription of the original manual, “Visit the Sage” and loading instructions).
The earlier #9 historical acceptance record is not rewritten. The #10 failed
attempt does not prove a regression or establish the cause of the missing save;
the explicit-save repeat supplies the current bounded recovery evidence.

RVDB final regression: **407 passed**. Fresh source validation: **59 valid entities**,
zero schema/relationship errors. Two temporary builds, canonical bundle and installed
bundle match byte-for-byte at the recorded SHA-256. No RVDB file changed. All 39
protected prior asset/core/bundle hashes still match. No historical cache was deleted.


## Final implementation checkpoint

Final RetroVault regression: **2,489 passed in 48.44 seconds**; RVDB: **407 passed**.
All five agreed ten-minute sessions have targeted human gameplay acceptance.
The original SNES sidecar failure remains recorded, resolved by the approved
private-directory repair with regression-first and controlled real-child evidence.
Post-repair live RetroArch save/reload runs also leave empty transient caches.
No repeat ten-minute session was required to prove the bounded cleanup repair.

The full suite covers preparation failure, failed-startup Stop recovery, repeated
Stop, second-launch rejection, natural exit, shutdown, unrelated-process protection,
save rollback and edition isolation. Sustained runners preserve their old smoke
limits and do not turn process survival into human acceptance. Save/reload uses
separate sessions and the existing maximum timeout; no claim is made that those
save sessions independently meet a ten-minute minimum.

Scope limits: five representative keyboard routes, ten minutes each, current
installed binaries/display; no every-game, physical-gamepad, two-player, multi-hour,
cross-core state portability, live geometry-switching or numerical memory-budget
claim. Production input/readiness/geometry and existing artwork/shaders remain
unchanged. Only primary temporary-file ownership changes in production.

Git diff/compile checks pass. No commits or pushes have been performed. Final
publication is pending the user's instruction; USQE #11–#12 remain unstarted.

## Closure authorization

The user approved committing and pushing all Milestone #10 work, then beginning
Milestone #11 planning. This closure commit contains the accepted implementation,
tests and evidence record. Earlier publication-pending statements describe previous
checkpoints. Exact publication hashes are reported after remote verification.
Milestone #11 implementation requires its delivery-policy review and approval.
