# USQE Milestone #11 — Safe RVDB delivery and rollback

Status: **COMPLETE within the approved manual delivery/rollback scope.**
Starting RetroVault checkpoint: `6debf74ec19fdc86b1155fd5f38139a794b1bf8e`.
RVDB checkpoint: `cc7b5e919f337910601738018b99c05007879c47` (unchanged).

## Approved policy and implementation

Manual local-file acquisition from the trusted RVDB producer, independently approved
SHA-256/full producer commit, existing consumer validation, atomic activation,
retention of the previous validated bundle, explicit offline rollback and restart
to apply. No automatic downloads, signing infrastructure or live knowledge reload.

`services/rvdb/delivery.py` owns staging, pin verification, one rollback checkpoint
and a destination lock. `scripts/install_rvdb_bundle.py` is the explicit CLI;
unpinned installation is deliberately rejected with a nonzero exit status.
The receipt records asserted provenance; it does not authenticate a commit by itself.
Existing RVDBConsumer/RVDBService validation and application ownership are unchanged.
The producer still owns source schemas, references and knowledge semantics.

The previous payload and intended candidate provenance share one atomically written
checkpoint before bundle replacement. An interruption between those replacements
leaves the old active bundle valid; checkpoint existence is not activation success.
Repeated same-byte installation and rollback are idempotent. Rollback does not
swap the current and previous versions. Missing/malformed active data can recover;
a different valid external installation is protected from accidental rollback.
Initial installation has no previous version. Invalid active data must be recovered
before a new install can replace the retained checkpoint.

## Verification and protected boundaries

Regressions were introduced before the delivery module. Focused checks exercise
actual CLI statuses, offline rollback after removing the source, bad pins/structure,
corrupt rollback metadata, write/flush/fsync/replace failure at checkpoint and
activation stages, temporary cleanup, idempotence, symlink protection, missing
backup, corrupted active data and concurrent delivery rejection. Full verification
results will be appended after completion.

Only temporary fixture destinations are used. Installed bundle and real user data
are not modified. RVDB schemas/canonical IDs, Library identity/persistence,
readiness/core selection, emulator execution, artwork and geometry remain protected.
No emulator session is needed. Old milestone records remain unchanged.

## Limits and delivery instructions

See [configuration/startup](configuration_startup.md) for exact commands and recovery
behavior. Portable structural compatibility is not a new semantic-version scheme.
Pin selection remains a trusted human/release decision. Local checksums do not defend
against an attacker with permission to rewrite the checkpoint. File fsync/atomic
replacement protects handled failures and process-interruption ordering, not every
power-loss/filesystem scenario. An abruptly killed command can leave inert staging
files; startup never uses them. No automatic deletion policy is added.

USQE #12 remains unstarted. The user approved formal closure and commit/push.


## Final verification

- Focused delivery/CLI checks: **23 passed**.
- Complete RetroVault suite: **2,509 passed in 32.94 seconds**.
- Complete RVDB suite: **407 passed in 8.77 seconds**; no producer changes.
- Source validation: **59 valid entities**, zero schema/relationship errors.
- Two fresh temporary builds equal the canonical and installed bundles byte-for-byte.
- Shared SHA-256: `4d99f2b1bff694f26ca1b1ff68b7d4d1816236abb1e64d10a62e14bf20e3eb43`.
- All 39 protected prior package/core/bundle checksums unchanged.
- Python compilation and Git whitespace checks passed.

The interruption regression stops between checkpoint and activation and verifies
safe retry/rollback. It does not claim exhaustive OS-crash or power-loss testing.
Actual subprocess tests verify success and nonzero failure statuses. No real-user
installation or emulator launch was performed. At the verification checkpoint, no
commit or push had been performed. No additional production
defect required scope expansion. Milestone #12 remains unstarted.

## Closure authorization

The user authorized completing Milestone #11 including normal commit/push. This
commit includes the verified implementation, tests, delivery instructions and
closure record. Exact commit and remote equality are reported after publication.
RVDB requires no source changes or new commit. The original roadmap and earlier
acceptance records remain protected; USQE #12 remains unstarted.
