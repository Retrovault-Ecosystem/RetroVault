# RetroVault + RVDB architecture contracts

Current implementation reference through **Milestone #12 — Advanced visuals**, 2026-09-30.

The six-boundary architecture remains unchanged. Earlier milestone sections retain
historical evidence; the ownership and presentation contracts below reflect the
current implementation. Milestones #5/#6 are re-closed following the Genesis
Library metadata correction and explicit user confirmation of correct operation.
See `current_milestone.md` and [configuration/startup contracts](configuration_startup.md). Milestone #7 remains complete; Milestone #8 preserves its startup and configuration contracts.

## Ownership and flow

```text
RVDB YAML + schemas -> validated producer build -> portable nodes/edges bundle
                                                        |
                                             RVDBConsumer -> RVDBService
                                                        |
                                                 RVDBLibraryResolver
                                                        |
Configured sources -> scanner -> physical Game inventory -> family/edition projection
                                      ^                         |
User stores --------------------------+-------------------------+
  |                                                             |
  +-> manual assignments + curated recommendations -> presentation intent
                                                                |
Selected edition + installed core + LaunchProfile -> production package policy
                                                                |
                            transient runtime layers -> RetroArch execution
                                                                |
                          lifecycle feedback + successful-launch recent history
```

User persistence is an input to library and presentation services, not a mandatory
serialization step between every pair of layers. Execution success is reported
back through the controller; runtime services do not write favorites or collections.

| Boundary | Owner and interfaces | Permitted responsibility | Must not become |
| --- | --- | --- | --- |
| RVDB knowledge | `rvdb/engine/loader.py` (`EntityLoader`), `engine/graph.py` (`RVGraph`), `validator/schema.py`, `validator/relationships.py`, `commands/build.py`, `build/builder.py` | Canonical entities, schema/relationship validation, portable exports | Local inventory, installed binaries, user preferences, host configuration |
| Consumer adapter | `services/rvdb/consumer.py` (`RVDBConsumer`), `service.py` (`RVDBService`), `models.py` | Bundle mechanics and typed application read models | A second RVDB engine or a writer of canonical knowledge |
| Local library | `services/library/source_manager.py`, `scanner.py`, `library_builder.py`, `library_service.py`, `canonicalization.py`, `game_variants.py`, `rvdb_resolver.py`, `models.py` | Physical discovery, enrichment, edition classification, visible projection | Canonical knowledge authoring or emulator execution |
| Persistence | `config/loader.py`, `config/writer.py`, `services/library/state.py`, `collections.py`, `import_sources.py`, `services/presentation/store.py` | Explicit user changes and durable preferences | Storage for transient launch configuration or inferred RVDB facts |
| Presentation | `services/presentation/factory.py`, `resolver.py`, `effective_resolver.py`, `composer.py`, `automation.py`, `recommendation_resolver.py`, `assets.py` | Resolve user intent and local recommendations | Asset deployment, process spawning, or persistence as a side effect of resolution |
| Runtime configuration | `models/launch_profile.py`, `services/presentation/platform_policy.py`, `production_package_resolver.py`, `production_package.py`, `services/retroarch/*_runtime.py`, `session_config.py` | Validate production qualification and compose disposable launch resources | A writer of permanent external RetroArch config or canonical knowledge |
| Execution | `services/retroarch/launcher.py`, `core_resolver.py`, `validator.py`, `services/presentation/process_lifecycle.py` | Installed-core lookup, preparation, process ownership, cleanup, lifecycle reporting | A library importer or user preference store |

Paths in the first row beginning `rvdb/` refer to the sibling RVDB repository;
its remaining paths are relative to that repository. Other rows are RetroVault paths.
RVDB's producer contract is also documented in its `docs/architecture.md`.

## Knowledge export and consumption

- YAML remains RVDB's canonical source; schemas define entity and relationship
  semantics. `commands/build.py` loads one fresh source snapshot, rejects empty
  sources and duplicate IDs, and validates schemas and relationship targets before
  exporting. Failed validation does not invoke the writer or replace an artifact.
- `build_bundle()` remains a low-level serializer for callers that already own
  validation. It does not itself certify arbitrary supplied graphs. `cmd_build()`
  retains its existing path-on-success / `None`-on-failure API and printed error.
- The portable envelope remains exactly `nodes` and `edges`. No mandatory version
  key is added. RetroVault does not import RVDB producer internals.
- `RVDBConsumer.reload()` validates node mappings, matching key/ID, non-empty type,
  optional string name, relationship mappings, and lists of non-empty target IDs
  before publishing a new snapshot. Read/encoding/JSON/structural errors become
  `RVDBError`; the last valid snapshot remains available on reload failure.
- Consumer validation is structural, not a duplicate schema engine. Missing target
  entities remain compatible with existing service fallbacks; unknown entity types
  may coexist. Missing edge entries remain tolerated. Embedded node relationships
  are not used to override the exported edge map.
- Raw consumer dictionaries remain mutable compatibility access. Their callers
  must not mutate them. Application code consumes `RVDBService` read models; the
  composition root may construct/inject the consumer. This is an ownership rule,
  not a claim that legacy dictionaries are physically immutable.
- `RVDBLibraryResolver` returns a unique normalized name/extension match or no
  match. RVDB support does not prove an installed core or a READY visual package.

## Identity and library snapshots

| Identity | Meaning and use | Not interchangeable with |
| --- | --- | --- |
| `rvdb_platform_id` | Canonical platform knowledge and platform policy key | A display name or installed core filename |
| `rvdb_game_id` | Canonical title knowledge | A physical dump, edition, path, or user persistence key |
| `local_file_id` / `game_identity(game)` | Registry-owned opaque local file ID; favorites, recent history, collections, game assignments. Unregistered compatibility callers retain resolved-path fallback. | RVDB title identity, current location, or a content hash |
| `rom` / `location_key(rom)` | Current launch location / normalized discovery location | Permanent identity or extracted runtime content |
| `family_key` | Derived grouping for the visible library projection | A new durable persistence identity |
| `archive_member` | Selected content within a container for execution | Independently persisted ownership of that archive member |

`LibraryService._physical_games` owns the complete physical inventory;
`LibraryService.games` is the canonical family/edition projection. Hidden editions
remain launchable. Refresh updates all `Game` fields, including variants, while
preserving surviving visible object identities and matching physical representatives.
A failed refresh restores sources, physical inventory, visible list, and prior
object state together. The existing scanner, state application, artwork enrichment,
and canonicalizer remain the rebuild path. Bulk import uses the same services.

Milestone #3 adds durable local identities without replacing this pipeline.
`IdentityRegistry` stages registration after discovery and before applying state.
It collapses duplicate resolved locations from overlapping sources, retains separate
identities for separate copies, and reconnects a missing file only when its content
fingerprint and platform context identify one unambiguous candidate. A changed
content fingerprint at the same path receives a new identity. Later RVDB enrichment
at an unchanged location does not change the local ID.

The visible family projects membership from all currently represented editions.
Favorites and collections add the preferred edition; removal clears all represented
edition memberships. Recent history records the actual selected physical edition
only after launch success. Gallery and Systems views resolve these IDs to current
families, counting each family once. Edition-specific presentation assignments do
not transfer when the preferred representative changes. Extracted runtime ROM paths
never replace the selected edition's persistence identity.

## Durable and disposable storage

| Data | Current owner/location | Classification |
| --- | --- | --- |
| Settings and source definitions | `ConfigLoader`/`ConfigWriter`, `runtime.json` under XDG config home; `config/retroarch.yaml` defaults | Durable user overrides plus repository defaults |
| Local file identities | `IdentityRegistry`, `library-identities.json` beside library state | Durable registry, version 1; never disposable cache |
| Favorites/recent history | `LibraryState`, `library-state.json` | Durable, local-file keyed; version 2 with legacy read support |
| Collections | `CollectionStore`, `collections.json` | Durable, local-file keyed; version 2 with legacy read support |
| Presentation assignments | `PresentationStore`, `presentation-state.json` | Durable default/platform/local-file assignments; version 2 with legacy read support |
| Physical inventory and family projection | `LibraryService` memory, rebuilt from configured sources | Derived state |
| Archive scan results/extracted content | `ArchiveScanCache`/`ArchiveRuntime` | Rebuildable cache, never launch validation authority |
| Primary/session/core/overlay/shader/contain/cheat configuration | Existing runtime services | Disposable launch artifacts |
| Installed native visuals | `NativeVisualService` and native deployment services | Explicitly installed assets, not disposable session configuration |

Stores use temporary-file replacement; this is not a cross-store transaction or
multi-process locking guarantee. The historical durable baseline's `config.json`
and `library.json` do not establish active production read/write ownership today.
The current code uses `runtime.json` and source reconstruction. Do not delete or
migrate historical user files based solely on this observation.

Since Milestone #7, active primary/session/core/overlay/shader, archive and probe
owners use the shared XDG cache helpers. Explicit injected directories still take
precedence. Older cache directories are not migrated or deleted automatically.

## Presentation intent versus production authority

1. `PresentationResolver.resolve_with_sources()` resolves each manual field through
   local-file game -> canonical platform -> default -> empty, recording its origin.
   Empty means inherit, not explicit disable. Existing `resolve(game)` remains supported.
2. Automatic game/platform references fill only empty manual fields. Compose references
   before filesystem resolution so an unused missing recommendation cannot invalidate a
   manual override. A selected missing portable asset remains an error.
3. `PresentationCompositionFactory.build()` preserves intent resolution for existing
   callers. `build_launch()` supplies one configuration snapshot and the same intent
   components to `LaunchPresentationResolver`. Its immutable `LaunchPresentation` result
   separates requested references/origins from selected assets, package authority and errors.
4. Canonical READY platforms select the existing qualified package, superseding requested
   overlay/shader preferences. Superseded assets need not exist. Canonical UNCONFIGURED
   platforms fail closed; unknown/legacy platforms retain manual/recommendation semantics.
   Artwork intent remains frontend/library data; it is not selected as an emulator overlay.
5. Package identities are relative to configured overlay/shader roots, shared with native
   installation and discovery. Root symlinks are supported; package symlinks escaping a
   root are rejected. Missing packages never silently fall back to `/opt/retropie`.
6. Studio and Native Visuals consume launch selection while displaying stored preferences
   separately. Studio reports per-field intent origins and package/unavailable status;
   package pinning is disabled, while clearing stored overrides remains available.
7. Game Details delegates to `GameLaunchController`, which uses the shared selection
   for the chosen physical edition. A launch selection failure prevents preparation
   from continuing. The launcher independently
   revalidates package/core selection and current configured roots before creating runtime
   resources, so a preview is not a cached launch authorization.

Resolution never installs assets, writes user preferences, prepares runtime files or
spawns an emulator. Installation remains an explicit NativeVisualService operation.
Native shader `portable_reference` is a package-source locator; `assignment_reference`
is the installed `retro-vault://shaders/retrovault/...` reference. Existing reference
formats and stored assignments are preserved without heuristic migration.

`CoreMapper` currently derives local qualified-core filenames from
`PlatformPresentationPolicyRegistry`. These are RetroVault qualification choices,
not a replacement for all RVDB compatibility knowledge. Multiple candidate cores
must not be silently treated as a unique choice. Core installation is checked
separately by `CoreResolver`, using exact normalized identities and host-native
binary suffixes. Distinct matching installations are ambiguous; filesystem ordering
never chooses a winner. Symlink aliases to the same binary collapse to one candidate.
Explicit binary paths are checked directly. `CoreMapper` accepts canonical platform
IDs as well as historical display aliases, and the scanner prefers canonical IDs.

Production packages own the presentation envelope. Core-reported display aspect
feeds contain geometry and, where enabled, the matching adaptive opening. Shader
and inherited RetroArch state must not introduce competing geometry authorities.
This milestone does not change assets, aspect rules, accepted NES/SNES calibration,
or readiness assignments. Live mid-game aspect qualification remains separate.

## Runtime and execution contract

- `MainWindow` constructs the shared launcher with the configured executable.
  Standalone `GameDetails` does the same. Validation uses the shared launcher's
  command; the content-aspect probe and visible process use that same command.
  Legacy injected test/adaptor launchers without a command retain config fallback.
  The executable remains a construction-time snapshot. Presentation asset roots are
  reread for launch; changing them does not reconstruct an active emulator session.
- `LaunchProfile.config`, when supplied, is the source for `PrimaryConfigRuntime`.
  It is copied and isolated even when no video-driver override is requested.
  Exactly one resulting primary `--config` is used. The persistent source is not
  appended again or edited. Failure to isolate an explicit source prevents launch.
- Without an explicit primary config, existing discovery/host driver qualification
  remains. On hosts with no driver override this may produce no primary copy;
  universal qualification on those hosts is not established by this milestone.
- Session baseline clears inherited presentation state, followed by selected overlay
  configuration, optional cheats, then final contain geometry. These ordered layers
  are passed in one pipe-delimited `--appendconfig` argument. Shader selection uses
  the existing transient shader path and enablement contract.
- READY launches may run a bounded headless content-aspect probe. It owns a process
  group and is terminated/reaped before the visible launch begins. Preparation is
  therefore not side-effect-free. Never mass-launch a library corpus for validation.
- `RetroArchLauncher` owns the visible process session/group, rejects a second active
  launch, and provides stop/exit cleanup. Session artifacts are disposable; reusable
  extracted archives are intentionally retained. `ProcessLifecycleAdapter` reports
  lifecycle state; hardware indicators do not choose geometry or own processes.
- Launch success means process creation succeeded, not that a game was proven
  playable. Recent-history write failure does not undo an already running process.

## Historical export discrepancy — resolved in Milestone #2

The Milestone #1 read-only audit found 53 valid source entities, but 57 in each distributed
bundle. Bundle-only entities:

- `core.mame`
- `core.mupen64plus.next`
- `compatibility.core.mame.platform.arcade`
- `compatibility.core.mupen64plus.next.platform.nintendo.n64`

The bundles also extend `frontend.retroarch`, `platform.arcade`, and
`platform.nintendo.n64` relationships beyond current source. RetroVault's copy has
an additional edge entry for the N64 compatibility entity compared with RVDB's copy.

Historical SHA-256 values (preserved during Milestone #1):

- RVDB: `c64263bd84cf0c1e0c9359d0e280e28be13814142af6e356a2e484352850d9e9`
- RetroVault: `978aacf594b580f12c2cf8189bb33459280967074095c3d9caca6b6e2538c0fa`

At Milestone #1, source validation did not certify these extra bundle records and
a rebuild would have removed them. That discrepancy is resolved by Milestone #2;
the old hashes above remain audit history. The original Milestone #1 scope excluded
this repair. Automatic bundle distribution remains outside both milestones.

Other retained limits: MainWindow's bundled-data path is working-directory-relative;
production assets use fixed `/opt/retropie` paths; raw consumer access is mutable;
`RuntimePresentationSession` is not wired as the production live-aspect loop;
legacy `LibraryProvider`/`GameHistory` are not the active durable library architecture.

## Milestone #1 verification and scope (historical)

Existing consumer, library, presentation, and process suites remain authoritative
regression coverage. Added tests cover malformed/failed reloads, producer validation
before writing, refresh edition changes and rollback, executable consistency,
one isolated primary configuration, and XDG cache isolation. Dependency guards
check producer isolation, raw consumer imports, and pure presentation dependencies.
They are static import guards, not a general proof against dynamic imports.

Verification uses temporary config/cache directories and mocked emulator launches.
No live emulator or deployed-asset change is required. See the final verification
record below for actual results; tests do not establish new visual qualification.

Out of scope: milestones #2–#14, new emulators/platforms, bundle reconciliation,
identity migration, saves/cloud sync, UI redesign, native deployment, calibration,
a generic execution framework, automatic bundle distribution, and broad legacy cleanup.

### Verification record — 2026-09-28

Milestone #1 implementation and regression verification are complete. This does
not close the deferred knowledge discrepancy or begin another milestone.

- RVDB source validation: 53 entities; zero schema/relationship errors.
- Baseline RVDB suite: 370 passed.
- Baseline RetroVault suite: 1,821 passed, 24 failed because primary runtime ignored
  the temporary XDG cache root and attempted home-cache writes in the sandbox.
- Final RetroVault full suite: **1,864 passed**.
- Final RVDB full suite: **372 passed**.
- Focused contract/launch/library checks and static dependency guards: passed.
- Changed/new Python source parsing and both repositories' `git diff --check`: passed.
- Both bundle SHA-256 hashes above remain unchanged; both load through the hardened
  consumer. No bundle rebuild, user-state migration, deployment, or live emulator
  qualification was performed. Existing uncommitted calibration/startup work remains.

Commands used (run each suite from its own repository):

```sh
# RetroVault: persistent settings and XDG-aware cache writes isolated under /tmp.
QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME=/tmp/rv-m1-test-config XDG_CACHE_HOME=/tmp/rv-m1-test-cache .venv/bin/python -B -m pytest -q -p no:cacheprovider

# RVDB: build tests use temporary output paths, leaving checked-in bundles intact.
.venv/bin/python -B -m pytest -q -p no:cacheprovider
```


### Formal closure

The approved Milestone #1 acceptance criteria are closed in
[the current milestone record](current_milestone.md#ecosystem-milestone-1--architecture-contracts--complete).
The final closure audit added a negative regression proving that an explicit primary
configuration which cannot be isolated never reaches process creation. The final
full RetroVault suite passed 1,864 tests; RVDB remains at 372 passing tests.
The closure audit also rechecked both bundle hashes, consumer loading, source
validation (53 valid entities), and diff integrity. No further in-scope production
code repair was required. Deferred work remains explicitly outside this closure.


## Milestone #2 — source/bundle reconciliation

RVDB now has canonical YAML for `core.mame`, `core.mupen64plus.next`, and their
existing Arcade/N64 compatibility claims. The three platform/frontend relationship
updates restore already distributed knowledge. The existing validated producer
build now generates 57 nodes and 57 edge-map entries from 57 source entities.

The producer artifact and this checkout's local runtime copy are byte-identical:

`cbe52800852543f88bdaf033bb0d50e348ffe64368391498ff93d72a785610dc`

Every node payload is unchanged from the pre-reconciliation consumer bundle.
Historical evidence dates and playability values are preserved. Generated empty
edge entries and canonical sorting account for the artifact differences.
`RVDBService.retroarch_view()` now obtains frontend core relationships through the
exported edge map, including when embedded node relationships disagree or are
absent. It does not fall back to embedded relationships when the graph has none.

RetroVault intentionally ignores `data/rvdb/` in Git. The synchronized file is a
local runtime artifact, not a newly tracked file. RVDB's tracked bundle has a fresh
validated-build parity test; cross-repository synchronization is an explicit byte
comparison, documented in RVDB's `docs/architecture.md` under "Bundle delivery and
drift prevention". There is no required sibling checkout in either application's
runtime and no silent optional cross-repository test.

User stores, local library identity, presentation assignments, qualified core
mapping, native assets, and emulator execution are unchanged. In particular, N64
and Arcade remain UNCONFIGURED for production visuals despite their source-backed
compatibility knowledge. No live emulator qualification or new universal playability
claim is made. Milestone #1 remains closed; its deferred reconciliation item is now
resolved. Other documented limitations remain, and Milestone #3 has not started.


### Milestone #2 verification and closure — 2026-09-28

- Baseline: 1,864 RetroVault tests and 372 RVDB tests passed.
- Final full suites: **1,869 RetroVault tests passed; 375 RVDB tests passed**.
- Focused checks: 102 RetroVault and 20 RVDB checks passed before the full suites.
- Canonical source validation: **57 valid entities**, zero schema/relationship errors.
- Fresh validated build equals the tracked producer bundle byte-for-byte; reversed
  entity input order produces the same bytes.
- Explicit cross-repository comparison passes, with the shared SHA-256 above.
- Both pre-reconciliation node maps equal the final node map. Existing 53 source
  records differ only in the three approved relationship updates; four records added.
- Diff integrity and Python parsing pass. Changes outside approved files, including
  pre-existing startup/calibration edits, were checked against pre-milestone hashes.

The consumer graph-authority tests cover conflicting embedded relationships,
missing embedded relationships, and missing exported relationships. N64/Arcade
integration tests preserve evidence counts, core mapping, and UNCONFIGURED state.
No emulator was launched and no persistent user state or deployed assets changed.

See the [formal milestone closure](current_milestone.md#ecosystem-milestone-2--rvdb-sourcebundle-reconciliation--complete).
Changes remain in the working trees; no commit, push, or release is implied.


## Milestone #3 — Game/file identity and persistence — COMPLETE

Closed 2026-09-28. Earlier milestone closure statements describe their historical
checkpoints; the identity/storage sections above reflect the current contract.

### Registry and reconciliation

The registry belongs to RetroVault, never RVDB. Each record contains an opaque
`local-file:<UUID>` key, current resolved path, platform matching context, stat
signature, and SHA-256 of the physical file/container. The initial registration
reads all discovered file contents; unchanged signatures avoid repeated hashing.
Changed signatures trigger hashing even if content ultimately remains identical.
Signatures use device, inode, size, mtime_ns, and ctime_ns; they are cache hints,
not portable identities. A file changing during hashing or an unreadable file
aborts registration. A discovered file already absent at registration is omitted.

Matching considers all observations in that scan. Two identical new files cannot
both claim one missing identity, and multiple historical candidates remain
ambiguous. Existing identical copies remain separate, including separate hard-link
locations. Symlinks resolve to the existing canonical-location convention.
Unavailable/disabled/removed sources do not purge registry records or user state.
Newly discovered paths are kept as sticky legacy aliases: reusing a path must not
reassign old unresolved preferences to replacement content.

### Store migration and recovery

The existing stores own serialization and validation. `identity_migration.py`
coordinates their migrations; it does not introduce another preference store.
All stores are validated before committing the staged registry. The registry then
commits before any path-key migration, ensuring retries use the same allocated IDs.
Each existing store receives an atomically published `.pre-identity.bak` before
its first migration write. Each store write is atomic and migration is idempotent.
There is no multi-file transaction: if a later store or projection fails, completed
durable checkpoints remain and retry resumes safely. The prior in-memory Library
snapshot and surviving object fields are restored by refresh/bulk failure handling.

Known path keys migrate across favorites, recents, collections, and presentation.
Missing-file keys remain unresolved until the file is registered. Conflicting
presentation profiles are retained in the version-2 `legacy_games` mapping under
their original keys; the local-ID assignment wins. These retained conflicts are
excluded from resolution and future migration, so clearing an override cannot
resurrect an older profile. Default/system assignments remain unchanged.

Old Presentation Studio canonical-title keys that were never valid local file keys
remain retained, unresolved entries. They are not assigned by guessing a title's
physical edition. Studio now writes local file IDs, reads canonical platform keys,
and calls the same `resolve(game)` interface as production launches. Other
shader/overlay/native-visual assignment pages use the shared identity helper.

Back up the registry together with all three stores. It is durable user data;
deleting it as though it were a scan cache breaks the association with persisted
IDs. Unsupported versions, extra unsupported properties, and corrupt data fail
without being overwritten. Format upgrades require deliberate restoration of
matching backups when downgrading to an older application.

### Limits and exclusions

- Moves/replacements before initial registration cannot be reconstructed reliably;
  first migration can only bind legacy paths to the files presently there.
- Ambiguous copies are never automatically merged. A rename accompanied by
  incompatible platform context may require a new identity rather than a guess.
- Archive identity is container identity. Repacking can change its fingerprint;
  individual members have no independent persistent IDs in this milestone.
- Cached stat signatures assume ordinary filesystem change reporting; this is
  not adversarial tamper detection or a ROM authenticity verifier.
- Initial fingerprinting adds I/O proportional to the registered file contents.
  No background hashing service or large-corpus performance claim is introduced.
- Family identities, grouping policy changes, automatic garbage collection,
  multi-process locking, cloud sync, and save/save-state relocation are excluded.
- RVDB data/bundles, core/runtime composition, production geometry, and emulator
  execution remain unchanged. No live emulator or real user-state migration was
  performed during verification.

### Verification

The complete RetroVault suite passes: **1,902 tests**, including 33 new regression
cases. Coverage includes restart/move identity, changed content, identical copies,
ambiguity, overlap/symlinks, enrichment, hashing and write failures, malformed data,
resumable migration/backups, conflicts without resurrection, returning sources,
family projection, refresh/bulk rollback, Studio/production resolution, selected
physical-edition launch feedback, and archive container identity.

Both distributed RVDB bundles remain byte-identical with the Milestone #2 SHA-256
`cbe52800852543f88bdaf033bb0d50e348ffe64368391498ff93d72a785610dc`.
No RVDB source or producer file changed for this milestone. Existing prior milestone,
startup, and calibration work remains in place. Closure is in the working tree;
no commit, push, release, or clean-worktree claim is implied.


## Milestone #4 — Core selection/readiness — COMPLETE

Closed 2026-09-28. The existing selection, presentation, runtime, and execution
architecture is retained. No RVDB entities, bundles, local compatibility mappings,
production readiness assignments, user-state formats, or calibrated assets changed.

### Ownership and decision sequence

1. RVDB supplies canonical platform/core knowledge and scoped compatibility evidence.
   Its core entity IDs are not inferred Libretro filenames or installation records.
2. `CoreMapper` selects the sole local policy candidate, preferring canonical platform
   identity over display labels. Multiple candidates require an explicit selection;
   the derived historical CORE_MAP export is not a multi-core selection API.
3. `CoreResolver.selection()` checks requested identity against local policy when an
   explicit platform is supplied. Unknown/unsupported policies, incompatible requests,
   and multiple defaults produce distinct failures without choosing another core.
4. `CoreResolver.resolve()` returns a `CoreResolution`: status, normalized identity,
   selected path, candidate paths, and explanatory message. Resolution requires an
   exact normalized identity, readable nonempty regular binary, and host-native
   suffix. Explicit paths bypass directory search, not eligibility checks. Directory
   search is deterministic and fails closed on traversal errors. `find()` remains a
   path-or-None compatibility wrapper for unambiguous resolution.
5. Game Details rereads the configured core directory before core resolution and
   reports settings errors, missing/unusable installations, incompatibility, and
   ambiguity without launching or recording history. It retains the active launcher's
   command as executable authority. Changing executable settings does not silently
   reconstruct the shared launcher or interfere with an active process session.
6. `LaunchValidator` checks executable usability, readable nonempty core/content
   files, and optional canonical-policy compatibility. Executable command names use
   PATH lookup; explicit relative paths retain their path semantics. Shared libraries
   need read permission, not an executable bit. Reports retain retroarch/core/rom/ready
   boolean keys and add reasons. `ready` means these prerequisites passed, not proof
   of production qualification or successful emulation.
7. `RetroArchLauncher` repeats the common prerequisite checks before archive/config
   preparation or process creation, including eligible-core checks for canonical
   platforms. Existing unknown/legacy LaunchProfile semantics remain supported, with
   the same file prerequisites. Production package resolution is still authoritative:
   canonical UNCONFIGURED platforms fail closed; READY packages and core-policy
   compatibility must validate. Process-start errors remain handled at execution.

The Settings core-directory check reuses native readable/nonempty core-file rules.
It means a candidate core exists in that directory, not that every game's required
core is installed or that the platform is production-ready. RetroArch's existing
Settings version probe is retained. RVDB core/evidence views remain knowledge views.

### Compatibility and verification

Existing UI tests now mock structured resolution rather than depending on the host's
installed cores. Existing composition/lifecycle tests stub only filesystem checks;
their policy and runtime assertions remain active. New integration tests use actual
temporary executable/core/content fixtures with mocked process creation, so readiness
is exercised without launching an emulator.

- Full RetroVault regression: **1,933 passed**, including **31 new cases**.
- Focused new-readiness plus launcher/lifecycle regression: **92 passed** before
  the final integration additions and full suite.
- New coverage includes canonical-ID scanning despite display-name changes, aliases,
  exact-vs-substring matching, ambiguous installations, symlink deduplication,
  explicit paths, unusable binaries/directories, traversal errors, multiple policy
  candidates, PATH and relative commands, file permissions, fresh directory settings,
  configuration errors, selected-edition identity, direct-call guards, missing
  production assets, and installed N64/Arcade cores remaining UNCONFIGURED.
- Both RVDB bundle hashes remain
  `cbe52800852543f88bdaf033bb0d50e348ffe64368391498ff93d72a785610dc`.
- Python parsing and both repositories' diff integrity checks pass.

### Limits and exclusions

Filesystem readiness does not establish ABI compatibility, authentic core contents,
firmware availability, sandbox visibility, or gameplay correctness. Files can change
between checks and execution; spawn failures remain a separate result. No live
emulator qualification, binary ABI probe, firmware management, core installation,
automatic fallback, compatibility expansion, READY promotion, new persistent core
preferences/selection UI, Windows/macOS deployment work, or visual recalibration is
included. Existing policy currently has a single candidate per supported platform;
a future multi-core UI must consume explicit selection rather than weaken ambiguity
handling. New checks may expose empty files, duplicate installations, or accidental
substring matches that older lookup accepted.

Closure is recorded in the working tree. No commit, push, deployment, or clean-tree
claim is implied; earlier milestone and unrelated startup/calibration work is retained.


## Milestone #6 — Presentation/Overlay/Shader architecture — COMPLETE

Closed 2026-09-29 within the approved scope. This adds shared read-only launch selection;
it does not replace the existing precedence, package-policy, deployment or runtime services.

### Changes and verification

- Fixed eager resolution of superseded recommendations; added per-field provenance.
- Unified configured package roots across installation, previews and launcher validation.
- Distinguished saved preferences from production package selection in Studio and visual
  assignment pages. Failed production selection is shown as unavailable and blocks launch.
- Added an explicit installed shader assignment reference and registered the existing
  Genesis native overlay. Genesis installation was verified in temporary test roots.
- Full RetroVault suite: **1,964 passed**, including **22 new integration cases**.
  Coverage includes mixed precedence, selected/masked missing assets, edition identity,
  READY/UNCONFIGURED/legacy behavior, incompatible cores, root changes, symlinks/escapes,
  missing packages without host fallback, one factory config snapshot, no resolution
  side effects, Studio and Native Visuals agreement, clearing retained preferences,
  launcher revalidation, and native Genesis deployment/reference resolution.
- Bounded production-launch checks passed sequentially for NES (10.012 seconds), SNES
  (10.010 seconds), and Genesis (10.010 seconds), with successful Stop/shutdown and no
  remaining owned groups, transient files or cleanup errors. Logs contain no ERROR/WARN
  entries. Evidence: `build/milestone6/{nes-01,snes-01,genesis-01}/report.json` and logs.
- The persistent RetroArch config SHA-256 remained
  `df6aff21b9193f3a1e90420ce0255be14e4bf8255fdfb0e7fc96f96b9dfd064d`.
- Producer/consumer RVDB bundle parity remains
  `cbe52800852543f88bdaf033bb0d50e348ffe64368391498ff93d72a785610dc`.
- Diff integrity checks pass. No user-store migration, production asset deployment,
  RVDB modification, commit or push was performed in this milestone.

### Boundaries and limitations

The existing qualified visual assets, core policies, aperture geometry, shader behavior,
Genesis MVP correction and Milestone #5 user acceptance are preserved. The new bounded
runs verify runtime/path wiring and cleanup; they do not claim a new visual acceptance,
all-game compatibility, long-session stability or save round-trip qualification.

Manual preferences remain stored even when production policy supersedes them. Changing
an asset directory now requires the qualified package at that configured location;
installation is never automatic. Files can still change between preview, validation and
execution. Static package validation does not certify shader compilation or pixels.
`RuntimePresentationSession` remains outside production wiring; continuous geometry
adaptation, explicit disable semantics, new platforms, artwork/shader redesign, additional
RVDB presentation schemas and cross-platform qualification remain outside this milestone.


### Approved visual extension and final closure — 2026-09-29

The user extended the initial architecture-only scope above to include original
Genesis Model 1 artwork and consistent NES/SNES/Genesis branding, approved the final
images, and explicitly requested integration and closure. That approval supersedes
the earlier artwork-redesign exclusion for these specific assets.

All three production bezel packages are deployed and byte-verified. Genesis uses
its approved physical aperture and the existing AdaptiveBezelRuntime; no new runtime
architecture or shader changes were needed. Full suite: **1,967 passed**; final image
cleanup checks: **18 passed**. Three final bounded production runs passed lifecycle,
persistent-config preservation and cleanup checks. User artwork approval and
runtime-process evidence are recorded separately.

See [final visual qualification](milestone6_visual_qualification.md) for exact geometry,
evidence locations, deployment backups and limits. Milestone #6 is complete within
the approved scope. The following section records the subsequent milestone.


## Milestone #7 — Configuration/startup reproducibility — COMPLETE

Application resources are anchored to the checkout; user configuration and active
cache owners use shared XDG path resolution. ConfigLoader validates the merged
configuration, while ConfigWriter retains atomic replacement. StartupReport uses
the typed RVDBService boundary and reports setup problems without scanning or
resetting user data. Bundle installation is explicit, validated and atomic.

The executable remains fixed until restart. Each launch reads one fresh configuration
snapshot for presentation and primary-source selection. Source precedence is profile,
saved primary path, then existing automatic discovery. PrimaryConfigRuntime isolates
canonical presentation on non-Wayland sessions too, handles tab-separated assignments,
and rejects includes that would escape the standalone configuration contract.
Settings explain activation and permit an empty initial Library.

No RVDB knowledge/schema, durable identity/store formats, accepted artwork, or emulator
execution architecture were replaced. Full suite: 1,999 passed; final targeted checks:
82 passed. Three live platform runs passed with unchanged persistent configuration
and complete transient cleanup. See [contracts, qualification and limits](configuration_startup.md).


## Milestone #8 — UI responsibility cleanup

The six existing boundaries remain intact. This milestone moves application workflow
out of widgets; it does not introduce an alternative presentation or execution engine.

| Component | Responsibility after cleanup |
| --- | --- |
| `controllers/game_launch_controller.py`, `GameLaunchController` | Qt-independent selected-edition preparation, archive extraction, core/readiness checks, presentation selection, LaunchProfile construction, launch/lifecycle coordination, and successful-launch history callback. |
| `ui/library/details/game_details.py`, `GameDetails` | Edition/archive/cheat dialogs, status and warning display, favorite/collection controls, and commands delegated to the shared controller. |
| `ui/main_window.py`, `MainWindow` | Composition and shared controller injection into Library and Playlists, page coordination, Qt process polling, and application shutdown. |
| `services/settings/service.py`, `SettingsService` | Executable/path readiness checks, source-update construction, override persistence through ConfigWriter, activation results, and distinction between write failure and post-save refresh failure. |
| `ui/pages/settings_page.py`, `SettingsPage` | Inputs, dialogs, readiness display, source-selection controls, and saved-setting signals. Existing ImportSourceStore remains the source-management persistence owner. |
| `services/library/presentation_studio.py`, `LibraryPresentationStudioService` | Shared default/system/game assignment commands, identity checks, and saved/effective assignment state for Studio and asset pages. |
| `services/library/library_service.py`, `LibraryService` | System statistics using the existing family and local-file identity projection; unavailable values remain distinct from zero. LibraryController exposes this query to SystemsPage. |
| `services/library/game_variants.py` | Shared variant-category normalization, also used by the edition picker. |

The launcher still validates prerequisites and production packages independently.
Presentation resolution never acquires persistence or process-spawning side effects.
`NativeVisualService` retains explicit asset installation. Settings probes remain
synchronous with their existing timeout; this is not a responsiveness milestone.

The launch controller owns only cheat input files it generates for an attempt. After
the launcher has copied the input into its managed runtime database, the controller
removes that input on success or failure. Failed deletions retain ownership for retry
on the next launch or application shutdown; arbitrary caller-owned `.cht` files are
not swept. Cheat serialization precedes temporary-file creation, and write failures
remove the partial input. Archive extraction remains a reusable cache, not a session
resource. Reentrant launch preparation is rejected, and dialog callbacks are released
after the attempt so the shared controller does not retain widgets.

No RVDB source/bundle, durable identity/storage format, accepted artwork, shader,
core qualification, executable activation, or configuration-precedence changes were
made. Native platform expansion, UI redesign, asynchronous work, packaging, migrations,
and broad file splitting remain outside scope.


Milestone #8 is complete. Verification: **2,020 full-suite tests passed**, followed by
**166 focused checks** after removing workflow stdout diagnostics. NES, SNES and Genesis
15-second controller-driven runs from `/tmp` passed lifecycle/preservation/cleanup;
selected artwork and effective viewport settings matched the previous qualification.
Evidence and qualification limits are recorded in [the closure record](current_milestone.md).


## Milestone #9 — One complete platform pipeline (NES)

The existing qualification runner now has an isolated full-pipeline mode. It obtains
its Game from LibraryService.load, persists favorites/collections/presentation through
existing owners, supplies LibraryController.record_played to GameLaunchController,
and reconstructs state in a separate interpreter. It records per-stage failure and
never substitutes a fabricated Game or a report-only history callback in this mode.
The original bounded runtime modes remain available.

MainWindow supplies the same PresentationStore and resolver factory to both Library
and Playlists GameDetails. This fixes the missing Playlists dependency wiring exposed
by the integrated UI test; the launcher still revalidates production presentation.

NES platform identity and qualified FCEUmm selection do not imply canonical title
coverage or a change to RVDB's Mesen compatibility knowledge. Duck Tales 2 intentionally
retains an empty rvdb_game_id while durable local-file identity drives user state.

Technical verification passed: 2,035 full-suite tests, 28 final focused checks, and a
30-second live NES scan/persist/launch/stop/restart run with unchanged protected files.
The user confirmed correct visuals and gameplay after a requested repeat 30-second
run, which also passed the full pipeline. Milestone #9 is complete and closed.
See [qualification and limits](milestone9_nes_pipeline.md).


## Milestone #10 — Platform expansion

The complete-pipeline qualification now covers NES, SNES and Genesis. The runner's
case table identifies qualification targets and existing catalog references only;
it does not own extension mappings, core compatibility or READY policy. RVDB,
Library, user stores, presentation resolution, runtime configuration and execution
retain the owners documented above. No production service or schema change was needed.

Tests cover five file formats and mixed-platform identity/persistence across restart.
Ambiguous content, incompatible cores, mismatched packages and unconfigured Sega
platforms sharing Genesis Plus GX fail closed. Existing artwork and shader policy
remain unchanged. Full suite: **2,118 passed**. Human visual/gameplay acceptance is
recorded separately from technical evidence. See [qualification and limits](milestone10_platform_expansion.md).

Milestone #10 is complete and formally closed. SNES and the repeated Genesis run
received explicit user visual/gameplay acceptance. All three live pipelines passed
restart, preservation and cleanup checks. Milestone #11 has not started.


## Milestone #11 — Metadata/artwork

RVDBLibraryResolver retains canonical title/platform authority, deduplicates alias
candidates and permits only conservative unique retail-tag fallback through the
existing VariantClassifier. ArtworkService owns local cover resolution and uses
RVDB platform vocabulary without interpreting runtime package assets. Additive
Game cover provenance is in-memory only; local IDs and persistence formats remain
unchanged. LibraryService refreshes physical editions and family projections; Qt
views only render results. Cover changes cannot select cores, overlays or shaders.

Verification: 2,142 tests passed, including fresh-process enrichment/state recovery
and the existing three-platform pipeline regression. Isolated UI review confirmed
aspect-preserving covers and literal metadata. No runtime or asset changes required
a live emulator rerun. Milestone #11 is complete and formally closed; no approved
work remains.
See [contracts and limits](milestone11_metadata_artwork.md).


## Milestone #12 — Advanced visuals

The production package remains shader/overlay authority. Visual tuning is a bounded
non-geometric capability of that package, defined in visual_tuning.py. PresentationStore
version 3 adds optional platform/game adjustments while preserving version 1/2 reads
and existing assignments. Game tuning is keyed by local-file identity and guarded by
canonical platform. No RVDB facts or Library cover fields carry tuning.

LaunchPresentation and LaunchProfile carry semantic adjustments. The launcher validates
them independently before preparation and maps only supported controls to temporary
shader parameters. Probe and execution use identical merged parameter values; source
presets are not edited. Reset/inherit semantics are explicit and apply on next launch.
SNES runtime sidecar mode 6 reconciles preset geometry; Genesis has neutral-default
optional image treatment while retaining MVP orientation. Approved bezel images remain
unchanged. Full suite: 2,166 passed. Human visual acceptance remains separate from
technical qualification. See [contracts and evidence](milestone12_advanced_visuals.md).

Milestone #12 is complete and formally closed. All six default/adjusted live sessions
passed technical qualification, and the user approved both sets of visual/gameplay
results. No approved work remains; Milestone #13 has not started.
