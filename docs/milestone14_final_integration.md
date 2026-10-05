# Milestone #14: final integration and release readiness

Status: **Milestone #14 and the approved 14-milestone roadmap COMPLETE**.
Evidence date: 2026-10-05. The user approved the implementation report and authorized
this final two-stage commit/publication closure. No Milestone #15 or post-roadmap
implementation has begun. Deferred features are not claimed complete.

## Scope and protected baseline

The approved scope is A1 preparation failure containment, A2 owned-process Stop recovery,
A3 trustworthy producer release gates, A4 atomic bundle publication, B1 accurate standalone
settings feedback, and B2 current documentation. No architecture replacement was required.

Pre-M14 published checkpoints:

- RetroVault `feature/rvdb-foundation`: `5e33611e990e46f3378ba03b1b4fde6dd8a1cd0b`.
- RVDB `develop`: `43b9ad6759aee8794caef4b738e244b1b349b589`.

Both worktrees were clean and those branch heads matched GitHub during the read-only audit.
The baseline suites passed 2,198 RetroVault and 376 RVDB tests. A clean exported baseline
passed all 2,198 consumer tests after documented bundle installation.

Protected and unchanged: canonical knowledge schemas/IDs, durable user formats and real
user data, ROM/file/family identities, qualified platform/core policies, production package
contents, approved NES/SNES/Genesis logos/artwork/shaders/geometry, deployment, successful
launch semantics, backend process-group safeguards and existing Git history. No historical
cache files were deleted, production runtime assets modified or live gameplay launched.

## Current ownership and supported behavior

| Layer | Authority and implementation |
| --- | --- |
| Knowledge | RVDB `engine/loader.py` (`EntityLoader`), graph, schema/reference/relationship validators, `commands/build.py`, `commands/validate.py`, `build/builder.py`; consumer `services/rvdb/consumer.py` and `service.py` validate/read portable knowledge without importing producer internals. |
| Local library | `services/library/scanner.py`, `library_builder.py`, `rvdb_resolver.py`, `canonicalization.py`, `library_service.py`, `bulk_import.py` and `controllers/library_controller.py` own inventory, conservative matching, family projections and refresh/import. |
| User persistence | `services/library/identity.py`, `state.py`, `collections.py`, `identity_migration.py`, `services/presentation/store.py`, and `config/loader.py`/`writer.py` own durable local preferences and retryable migration. |
| Presentation intent | `services/presentation/factory.py`, `resolver.py`, `effective_resolver.py`, `launch_resolver.py`, `production_package_resolver.py`, `platform_policy.py` and `visual_tuning.py` resolve preferences and qualified packages. |
| Runtime configuration | `services/retroarch/primary_config_runtime.py`, `session_config.py`, core-options, overlay, shader, contain and cheat runtime components isolate managed launch configuration. |
| Execution | `controllers/game_launch_controller.py`, `services/retroarch/launcher.py`, `core_resolver.py`, `validator.py`, `services/emulators/snes9x.py` and `session.py` select the physical edition and route to the one shared owned backend. |
| Lifecycle/cleanup | `services/presentation/process_lifecycle.py`, hardware runtime/state, `EmulatorSession` and backend process-group helpers observe process facts and retain ownership until safe cleanup. |
| Feedback | `ui/library/details/game_details.py`, `ui/main_window.py`, `services/settings/service.py` and `ui/pages/settings_page.py` display outcomes without becoming execution or persistence authorities. |

RVDB compatibility knowledge is not an installed-core or production-readiness declaration.
NES uses locally qualified FCEUmm while the existing NES knowledge record includes Mesen;
that previously documented distinction is preserved. RetroArch remains the default.
The approved standalone route is native Linux Snes9x GTK for loose SNES `.smc`/`.sfc` files;
it does not promise RetroArch overlays/shaders. Existing user visual preferences remain stored.

## Implemented repairs

### A1: preparation error containment

The controller calls `launch_failed()` only for an actual `LAUNCH_REQUESTED` lifecycle.
Errors before that transition preserve their original message and leave idle/exited state
valid. The strict lifecycle precondition remains; exceptions are not broadly suppressed.
Tests cover idle/exited preparation errors, configuration errors, pending-launch failure,
cancellation, subsequent launch, no false history and temporary cheat-input cleanup.

### A2: failed-startup cleanup recovery

Stop eligibility follows the live process owned by the shared session, rather than the
current pane's successful-launch flag. The adapter still requires an owned live process
and delegates to the existing backend termination safeguards. Failed startup stays idle
with indicators off while cleanup is retried; it is not relabeled successful/running.
Successful running lifecycles still transition through Stop/exit. Direct-session Stop is
available when no hardware-indicator adapter is attached.

Controlled children exercise real RetroArch/Snes9x adapters, shared session, controller,
lifecycle and details UI. They verify a failed result with a retained child, blocked Stop,
retry, second-launch rejection in both routes, child termination, repeated UI Stop,
unrelated-child survival and generated RetroArch artifact cleanup. The RetroArch child
uses a generic fixture profile to avoid production presentation deployment; existing full
presentation suites verify the protected qualified platform paths separately.

### A3: producer release gates

`cmd_validate()` returns an explicit boolean and rejects duplicate IDs before graph
construction, matching build rejection. `cli.py` maps validate/build results to nonzero
failure exit codes, including the `v` alias; build's Path/None Python API remains intact.
Other command return conventions remain unchanged. Tests execute the real CLI entry point
in subprocesses outside the checkout with valid, empty, duplicate, invalid-schema,
missing-reference and unreadable source fixtures, plus publication failure.

### A4: atomic bundle publication

The builder serializes to a unique same-directory temporary file, flushes and fsyncs it,
preserves an existing output's access mode and atomically replaces the destination.
Failures remove temporary output and leave the previous valid bundle byte-for-byte intact.
Tests inject serialization, stream write, stream flush, fsync and replacement failures,
both with and without a prior output. Successful bytes and JSON formatting are unchanged.

### B1: truthful standalone save feedback

Standalone settings reuse `SettingsSaveResult`. A completed write followed by a failed
reread reports saved settings with a refresh warning and retains merged effective values.
A write failure remains a save failure. Tests cover service results, UI text and preservation
of unrelated settings. The internal caller now reads `result.config`; persistence format
and backend validation are unchanged.

## Verification evidence

Final results from the complete verification runs are recorded below. All test roots and
build outputs are temporary; no real persistence is rewritten for verification.

- RetroVault complete suite: **2,213 passed** (34.94 seconds).
- RVDB complete suite: **406 passed** (8.53 seconds).
- Focused RetroVault lifecycle/controller/UI/settings/standalone group: **192 passed**.
- RVDB focused release-gate/publication group: **36 passed**.
- Clean source-copy consumer suite, with documented bundle installation: **2,213 passed** (39.76 seconds).
- Source/schema/entity-reference/relationship validation: **57 entities, zero errors**;
  unique IDs, 57 graph nodes and 57 edge entries verified.
- Two fresh generated bundles, canonical producer output and installed consumer bundle:
  **byte-for-byte parity**, SHA-256:
  `0c32be3117d31830c5c2e4a8554b2c2f627ed7474c81dbc1697511e5afbf3b9a`.
- Compilation/import and diff integrity: **passed**; 326 RetroVault and 83 RVDB Python
  files compiled in memory, consumer import/validation passed for all four bundles,
  both repositories passed `git diff --check`.

The full suites include architecture boundaries, persistence durability/migration/rollback,
refresh/import/canonicalization, presentation authority, configuration ordering/isolation,
core/executable resolution, process termination/shutdown and runtime cleanup. Controlled
process tests supplement prior human gameplay acceptance; no new visual qualification is
claimed. In-memory compilation avoids source-tree bytecode writes.

Temporary diagnostic logs live under `/tmp/m14-final` for this verification session; they
are not durable release artifacts. The numerical results and bundle hash here are the
repository record. A copied working tree is not a committed checkout: final commit IDs
are recorded below for the exact unchanged implementation.

## Runtime-cache disposition

Read-only inventory found 3,101 primary-runtime configurations (355,669,498 bytes,
about 339 MiB; latest modification September 28), plus 39 older session/overlay/shader/
contain/cheat files dated September 25–27. These are stale transient remnants and cleanup-
policy debt, not expected permanent configuration and not proof of an ongoing current
successful-launch leak. In-memory ownership cannot safely identify every historical writer.
No RetroArch/Snes9x GTK process was present at the audit's process-name check.

Archive-runtime's 449 files (108,388,341 bytes) are intentionally retained extraction cache.
Archive member timestamps do not establish extraction age. Core-options and aspect-probe
roots were empty. No historical file was deleted. New isolated lifecycle tests verify
owned transient cleanup; native profiles/saves/logs and archive caches are not mistaken
for transient RetroArch artifacts.

## Final deferred-work register

| Item/type | Why deferred; impact and revisit trigger |
| --- | --- |
| Broad customization; future feature | Approved appearance remains default. Clarify evolving user preferences before a separately approved implementation. Does not block current qualified use. |
| 4:3/16:9/mixed grouping; presentation expansion | Preserve natural fit with no stretch/crop. Revisit before future platform design work, not during closure. |
| More platforms/cores/backends; compatibility expansion | Each needs evidence and qualification. Existing supported fixtures work; unsupported platforms remain unqualified. |
| FCEUmm and broader compatibility records; knowledge expansion | Preserve local qualification versus knowledge distinction. Revisit with researched canonical records. |
| Historical hardware behavior/controller/save policies; product research | Exhaustive requirements are not blanket implementation approval. Resolve remaining user decisions first. |
| Continuous mid-game geometry; compatibility limitation | Startup-qualified behavior remains. Revisit with concrete changing-geometry fixtures; unwired runtime presentation machinery is not claimed operational. |
| Historical cache reclamation and archive quotas; policy debt | Old residue consumes disk, retained archives are intentional. Revisit with ownership-safe maintenance requirements; no deletion now. |
| Concurrent writers/cross-file transactions; future concurrency | Current retryable single-application workflow remains. Revisit before multi-process persistence support. |
| Unknown legacy entries/public compatibility APIs; compatibility retention | Keep recoverable data and still-used callers. Remove only with evidence migration obligations have ended. |
| Automatic bundle delivery/installers/portability; deployment | Documented manual installation is required. Revisit for an explicit distribution target. |
| Very large library scheduling/indexing/virtualization; performance | Existing indexes/hashing/caches are reusable. Benchmark representative growth before adding frameworks. |
| Scalar relationships across graph/bundle; schema research | Current production relationships are lists. Revisit before introducing scalar relationship data; no schema redesign now. |
| Canonical boundaries/optional metadata; research | DSi, Jaguar CD, XEGS, additional Atari families/revisions and unsupported metadata require evidence. No speculative entities. |
| Rich compatibility evidence/BIOS/queries; future knowledge features | Not required for present bounded qualifications. Revisit through a separate RVDB contract proposal. |
| All-game/long-session/native save round-trip certification; qualification | Current evidence is bounded, not universal compatibility. Revisit with defined fixtures and acceptance criteria. |

Earlier source/bundle drift and approved M1–M13 feature work are resolved. Old statements
that all core relationships or production compatibility records are absent are historical:
selected Master System/SG-1000 and other records now exist. Broader coverage stays deferred.
Legacy readers and used discovery APIs remain intentionally preserved. No additional
closure-blocking defect was established beyond the audited repairs. Full-suite UI failures
encountered during implementation were obsolete successful-launch ownership expectations;
the tests now check the approved actual-owned-process contract.

## Approved closure and protected checkpoints

The user approved the complete implementation report and explicitly authorized final
closure, commits, push and remote verification. Formal closure occurs in Milestone #14;
no Milestone #15, replacement roadmap or deferred implementation has begun.

Paired implementation/test checkpoints:

- RetroVault `feature/rvdb-foundation`: `a8730b75a727d5b0401abf67bf2bf1297d60f689`.
- RVDB `develop`: `94c57f030d88c3d6c2c2e1366d5a827a85df11b3`.

These hashes identify the tested implementation exactly. Subsequent closure commits contain
only the approved documentation. The final documentation-inclusive local/remote HEADs are
reported in the final protected-checkpoint response; a document cannot contain its own
containing commit's hash. The earlier published checkpoints remain intact in history.

Publication is limited to RetroVault `feature/rvdb-foundation` and RVDB `develop`, without
force-push, default-branch merge or release publication. Final acceptance requires source
manifest equality, compilation/import integrity, unchanged bundle parity/hash, intended
commit inventories, clean worktrees and matching local/remote heads with zero divergence.
A failed pre-push integrity check stops publication; a failed push or remote check must be
reported instead of claiming the protected publication succeeded.

All approved repairs and verification are complete. The deferred-work register above is
part of roadmap closure, not authorization to begin those items. Future development requires
a separately approved scope that preserves these protected contracts and checkpoints.
