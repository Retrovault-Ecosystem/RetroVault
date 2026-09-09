# RetroVault Current Milestone

## Project State

Project:

RetroVault

Repository:

`Retrovault-Ecosystem/RetroVault`

Active branch:

`feature/rvdb-foundation`

Protected RVDB repository:

`Retrovault-Ecosystem/RVDB`

Protected RVDB branch:

`develop`

---

## RVA1-B.7 — RVDB Consumer Boundary Closure

Status:

**COMPLETE**

RVA1-B.7 established the protected application-owned boundary between
RetroVault and RVDB.

RetroVault application code no longer depends directly on raw RVDB bundle
structures or on `RVDBConsumer` below the composition/infrastructure layer.

The application-facing boundary is now `RVDBService`.

### Final Architecture

MainWindow
    |
    +-- RVDBConsumer
    |
    +-- RVDBService
    |
    +-- RVDBLibraryResolver
              |
              v
       LibraryController
              |
              v
        LibraryService
              |
              v
        LibraryBuilder
              |
              v
          RomScanner

Application UI consumers receive `RVDBService`.

The Library scanner receives `RVDBLibraryResolver`.

`RVDBLibraryResolver` consumes `RVDBService`.

`RomScanner` does not locate, open, or bootstrap the RVDB bundle.

---

## RVA1-B.7 Closure Guarantees

The completed boundary guarantees:

- `ui/main_window.py` is the sole production owner of the RVDB bundle path.
- `RVDBConsumer` remains an infrastructure/bootstrap dependency.
- `RVDBService` is the application-facing RVDB knowledge boundary.
- SystemsPage consumes `RVDBService`.
- RetroArchPage consumes `RVDBService`.
- LibraryPage and GameDetails consume `RVDBService`.
- `RVDBLibraryResolver` consumes `RVDBService`.
- `RomScanner` consumes an injected Library resolver only.
- raw RVDB bundle dictionaries do not cross into application UI code.
- raw RVDB relationships do not cross into application UI code.
- Library ambiguity policy remains local to `RVDBLibraryResolver`.
- no-RVDB Library fallback behavior remains supported.
- protected RVDB source remains unchanged.

---

## RVA1-B.7 Checkpoint History

Key checkpoints:

- `82db3e6` — add RVDB application service boundary
- `3cb831b` — add typed RVDB systems service boundary
- `0b83602` — migrate SystemsPage to RVDB service
- `f3b0cfd` — migrate RetroArchPage to RVDB service
- `9b7db85` — expose platform extensions through RVDB service
- `e3111ea` — migrate Library resolver to RVDB service
- `e4be2b6` — route Library UI through RVDB service
- `52cb94c` — inject RVDB resolver into Library scanner

Technical closure checkpoint before documentation:

`52cb94ccd36995f2a574c5bc176342255b1142af`

---

## Regression Baseline

Current RetroVault regression baseline:

`71 passed`

---

## Protected RVDB Boundary

Protected RVDB checkpoint:

`1e8bb5d19014fbd0db5b99bc4da382064a44a438`

Required invariant:

- RVDB local HEAD remains at the protected checkpoint.
- `origin/develop` remains at the same protected checkpoint.
- the RVDB worktree remains clean.
- RetroVault consumes RVDB without modifying the protected RVDB source.

---

# Current Milestone

## RVA1-C — Application Development from the Protected RVDB Service Boundary

Status:

**IN PROGRESS**

RVA1-C begins normal RetroVault application development on top of the
completed RVDB consumer boundary.

The protected architecture established by RVA1-B.7 must remain intact.

Application features should consume RVDB through:

- `RVDBService`
- typed models in `services.rvdb.models`
- application-specific abstractions such as `RVDBLibraryResolver`

Application code should not bypass the service boundary by directly
interpreting portable RVDB bundle dictionaries.

---

## RVA1-C First Operation

The first RVA1-C operation should be a read-only application baseline audit.

Goals:

- capture the current runnable application structure;
- verify startup behavior with RVDB available;
- verify graceful behavior with RVDB unavailable;
- inventory the existing pages and functional surfaces;
- identify the first user-facing application feature milestone;
- preserve the completed RVA1-B.7 consumer boundary.

No RVDB foundation change is implied by RVA1-C.

---

## Continuation Instruction

To continue the RetroVault project in a future session:

> Continue RetroVault Project. Read `docs/current_milestone.md` and continue from the current milestone.

The milestone document is the authoritative continuation point for
RetroVault application development.

---

## RVA1-C.3-A — First Playable Workflow

Status:

**COMPLETE**

RetroVault has completed its first verified real-game launch through the
RVDB-backed application architecture.

### Safety Checkpoint

The first-launch safety work was established before allowing a real process
launch.

RetroVault checkpoint:

`98d9d7a66e11ec4ce2203eb2504067c754eda788`

The checkpoint protects:

- blank and unresolved RetroArch core handling
- exact RetroArch launcher command construction
- optional RetroArch configuration command construction
- process-spawn failure handling
- the process boundary through mocked `subprocess.Popen`

Regression baseline:

**82 passing tests**

### Verified Real Launch

The first successful controlled playable workflow used:

Game:

`Duck Tales 2 (U)`

Platform:

`Nintendo Entertainment System`

RVDB platform identity:

`platform.nintendo.nes`

ROM:

`/home/oilcan/roms/Starter Suite Roms/Nintendo Entertainment System/Duck Tales 2 (U).nes`

Requested RetroArch core:

`fceumm_libretro.so`

Resolved RetroArch core:

`/opt/retropie/libretrocores/lr-fceumm/fceumm_libretro.so`

RetroArch executable:

`/usr/bin/retroarch`

The replacement ROM was verified before launch as:

- present as a regular file
- non-empty
- 131088 bytes
- recognized as an NES ROM image
- carrying the standard NES/iNES signature
- reporting 8 PRG ROM banks
- structurally suitable for the controlled launch

SHA-256 captured during verification:

`c842683db5bd5a21bfc796903a733f4772a612709d10e9c880e76159963bddda`

### Verified Application Path

The successful real workflow established:

RetroVault
    |
    v
Library
    |
    v
ROM discovery
    |
    v
RVDB platform identity
    |
    v
CoreResolver
    |
    v
LaunchValidator
    |
    v
RetroArchLauncher
    |
    v
RetroArch
    |
    v
FCEUmm
    |
    v
Duck Tales 2 (U)

Before process execution, launch validation reported:

retroarch = true
core      = true
rom       = true
ready     = true

The controlled application session then established by direct observation:

- RetroVault opened normally
- the replacement ROM was discovered by RetroVault
- the game was identified as Nintendo Entertainment System
- RVDB identity resolved to `platform.nintendo.nes`
- the requested FCEUmm core resolved successfully
- RetroArch launched
- Duck Tales 2 (U) launched
- game video/display execution succeeded
- game audio succeeded
- the application and RetroArch exited normally

This is the first verified playable end-to-end RetroVault workflow.

### Runtime Observation

The successful launch emitted the following non-blocking Fontconfig warning:

`Fontconfig warning: using without calling FcInit()`

The warning did not prevent:

- RetroArch startup
- core loading
- ROM execution
- game display
- game audio

It is therefore recorded as a non-blocking runtime observation and is not a
closure blocker for RVA1-C.3-A.

### Repository Protection

The successful controlled launch made no repository changes.

At completion:

- RetroVault remained clean
- RetroVault remained synchronized with GitHub
- protected RVDB remained clean
- protected RVDB remained synchronized with `origin/develop`
- the 82-test RetroVault regression baseline remained established

### Closure

RVA1-C.3-A is complete.

RetroVault is now demonstrably playable through its RVDB-backed application
workflow.

Future application work must preserve:

1. the protected RVDB consumer boundary
2. deterministic core resolution
3. launch validation before process execution
4. the tested RetroArch process boundary
5. the established playable workflow
6. the current regression baseline unless intentionally expanded


---

## RVA1-C.4-E — Configurable Settings Workflow

Status:

**COMPLETE**

RVA1-C.4-E establishes the first controlled user-editable runtime configuration
workflow in RetroVault.

The Settings page now provides application-owned controls for the active
RetroArch executable, RetroArch core directory, and ROM library source while
preserving the protected RVDB consumer boundary.

### Published Technical Checkpoint

RetroVault implementation checkpoint:

`da07161e4c0d38957d2e2c2a048baf82f3f55d28`

Commit:

`feat: refine configurable settings workflow`

The implementation checkpoint contains only:

- `ui/pages/settings_page.py`
- `tests/test_settings_page.py`

### Settings Workflow

The completed Settings workflow provides:

- editable RetroArch executable path
- editable RetroArch core directory
- editable ROM library path
- compact path editors
- path descriptions inside the editors
- Browse controls for all configurable paths
- dynamic editor sizing for longer paths
- bounded maximum editor width
- Restore Default Paths
- explicit Save Runtime Settings
- validation controls with actionable status
- immediate revalidation after restoring defaults
- responsive native file/directory selection behavior
- no automatic persistence merely from editing or browsing

The Settings layout intentionally avoids redundant display-only path text where
the editable controls already communicate the active value.

Every visible path/status control therefore has an application purpose.

### Semantic RetroArch Validation

RetroVault does not accept an arbitrary executable merely because it exists.

The RetroArch executable validation surface verifies that the selected program
behaves as RetroArch.

The validated real executable remains:

`/usr/bin/retroarch`

A deliberately incorrect executable such as:

`/bin/ls`

is rejected by the semantic validation path.

This prevents a user from accidentally saving an unrelated executable as the
RetroArch runtime.

### Semantic Core Directory Validation

The configured RetroArch core directory is validated as a usable libretro core
location rather than merely as an existing directory.

The validated current core root remains:

`/opt/retropie/libretrocores`

The Settings workflow therefore protects the established playable launch path
while still permitting installations whose valid RetroArch/core locations
differ from the development defaults.

### Library Configuration

The ROM library source is user configurable.

The current effective development library remains:

`/home/oilcan/roms`

The library source identity is preserved when its path is changed.

The Settings persistence workflow preserves:

- source `id`
- source `name`
- source `enabled` state
- source `type`

while replacing the configured source path.

Library discovery remains recursive through the established scanner workflow.
The previously verified Duck Tales 2 ROM was successfully discovered below
nested library directories.

### Configuration Persistence Boundary

Settings writes are routed through `ConfigWriter`.

Editing a field does not write configuration.

Using a Browse control does not write configuration.

Restoring default paths does not write configuration.

Persistence occurs only through the explicit Save Runtime Settings action after
validation succeeds.

Existing unrelated runtime overrides are preserved by the writer workflow.

### User Configuration Protection

During implementation, regression testing, validation, and final audit, the real
user runtime configuration remained protected.

Validated runtime file:

`~/.config/retrovault/runtime.json`

Validated SHA-256 at closure:

`3512b4d623d5101ea96a0cf02bb1c76e68a4db8d4bfbdc8bc185abc39af765ff`

Legacy user files also remained preserved:

- `~/.config/retrovault/config.json`
- `~/.config/retrovault/library.json`

### Settings Regression Coverage

Final Settings-specific regression baseline:

**46 passing tests**

The Settings tests cover the established workflow including:

- effective configuration display
- runtime override detection
- no-write initialization
- explicit runtime persistence
- preservation of unrelated overrides
- editable library persistence
- library source identity preservation
- invalid library rejection
- internal path descriptions
- Browse controls
- dynamic path editor sizing
- default restoration
- actionable path validation
- semantic RetroArch executable validation
- semantic libretro core validation
- no-write Browse behavior
- no-write Restore Default Paths behavior
- immediate status revalidation
- test collection integrity

Duplicate test definitions discovered during the final integrity audit were
removed before closure so every Settings test has a unique collected identity.

### Regression Baseline

Current complete RetroVault regression baseline:

**143 passing tests**

This supersedes the earlier RVA1-C.3-A baseline of 82 passing tests.

### Protected RVDB Boundary

Protected RVDB checkpoint remains:

`1e8bb5d19014fbd0db5b99bc4da382064a44a438`

Required invariant remains satisfied:

- RVDB local HEAD remains at the protected checkpoint
- `origin/develop` remains at the same checkpoint
- the RVDB worktree remains clean
- Settings configuration does not modify RVDB
- application code continues consuming RVDB through the protected service boundary

### Closure

RVA1-C.4-E is complete.

RetroVault now has a tested, explicit, user-facing runtime configuration
workflow without weakening the established playable application path or the
protected RVDB architecture.

Future application work must preserve:

1. the protected RVDB consumer boundary
2. the verified playable workflow
3. semantic RetroArch executable validation
4. semantic core-directory validation
5. explicit-only configuration persistence
6. user configuration protection
7. recursive library discovery
8. the current 143-test regression baseline unless intentionally expanded

---

## Next Application Operation

With RVA1-C.4-E complete, the next RetroVault application milestone must begin
from the published Settings checkpoint and the protected RVDB service boundary.

Before selecting or implementing the next user-facing feature, perform a
read-only application-state audit covering:

- current page capabilities
- current Library workflow
- current Systems workflow
- current RetroArch workflow
- current Settings workflow
- remaining placeholders or non-functional controls
- the next highest-value user-facing application capability

The audit must preserve the established application invariants and must not
modify the protected RVDB repository.

The next milestone identifier and scope should be established from that audit
rather than assumed in advance.

## RVA1-C.5-B.7 — Artwork Integration Closure

Status:

COMPLETE

RetroVault artwork integration is now established as a
durable application capability.

Established behavior:

- artwork configuration is exposed through the application
  Settings surface
- the effective artwork directory is persisted through the
  runtime configuration layer
- artwork discovery is owned by `ArtworkService`
- artwork discovery recursively indexes supported local image
  files
- artwork lookup is based on ROM identity rather than display
  name alone
- explicit artwork assignments take precedence over discovery
- filename matching is case-insensitive
- ambiguous same-stem artwork is rejected rather than guessed
- platform-aware disambiguation resolves otherwise ambiguous
  artwork when the filesystem path supplies a matching platform
  component
- artwork lookup results are cached by ROM identity
- changing the artwork directory invalidates the artwork index
  and cache
- library games are enriched with resolved artwork through the
  library service
- artwork can be refreshed through the running application
  without restarting RetroVault
- Settings artwork-directory changes propagate through the
  controller and library presentation
- Game Details renders resolved artwork
- Gallery game cards render resolved artwork
- Gallery artwork preserves aspect ratio and uses smooth
  transformation
- missing or invalid artwork safely falls back to the existing
  controller placeholder
- Gallery reconstruction reflects refreshed artwork

Validation established during B.7 closure:

- direct Gallery artwork presentation regression: 5 passed
- targeted Gallery/artwork regression: 123 passed
- targeted artwork closure baseline: 178 passed
- complete RetroVault regression: 271 passed
- compile gate: green
- no genuine artwork TODO/FIXME implementation debt identified

Published implementation checkpoint before documentation closure:

- `f70957e1d2ca16b66ba32085317e3aefa7a3d8c2`
- `feat: harden gallery artwork presentation`

Protected RVDB consumer boundary:

- RVDB remains unchanged at
  `1e8bb5d19014fbd0db5b99bc4da382064a44a438`
- RetroVault continues to consume RVDB without modifying the
  protected RVDB repository

Closure decision:

RVA1-C.5-B.7 artwork integration is complete.

No additional B.7 production increment is required merely to
extend the milestone numbering. Future artwork capabilities may
be introduced as new feature work when justified by application
requirements.

Next operation:

- begin from the clean post-B.7 application checkpoint
- determine the next RetroVault application milestone from the
  current production surface
- preserve the protected RVDB consumer boundary

---

## RVA1-C.6-A — Manual Named Collections

Status:

**COMPLETE**

RVA1-C.6-A establishes the first complete manual
collection and playlist workflow in RetroVault.

### Established User Workflow

RetroVault now supports:

- creating named manual collections
- case-insensitive collection-name uniqueness
- renaming collections while preserving membership
- guarded collection deletion
- adding the selected Library game to a collection
- preventing duplicate game membership
- preserving insertion order within a collection
- removing selected games without deleting them from the Library
- persistent collections across application restarts
- collection browsing through the Playlists page
- full Game Details for selected playlist games
- artwork rendering or safe controller fallback
- favorite management from playlist Game Details
- adding a playlist game to another collection
- launching playlist games through the established RetroArch path
- safe clearing when a collection or game selection becomes empty

The live workflow was verified with the user-owned collection:

`NES Favorites`

The collection persisted across restart and contained the
verified Duck Tales 2 game without duplicate membership.

### Collection Persistence Boundary

Collection persistence is owned by:

`services.library.collections.CollectionStore`

The application-owned persistence file is:

`~/.config/retrovault/collections.json`

The format is versioned independently from favorites and
Recently Played state.

Collection membership uses the existing normalized ROM identity
contract supplied by `game_identity`.

Writes are atomic and use a temporary file followed by
`os.replace`.

The collection store rejects:

- empty collection names
- case-insensitive duplicate names
- invalid JSON structures
- unsupported persistence versions
- non-string game identities
- duplicate persisted collection names

### Application Boundary

Collection operations are exposed through:

`CollectionStore`
→ `LibraryService`
→ `LibraryController`
→ application UI

The Playlists page and Game Details do not open or interpret the
collection JSON file.

Saved identities are resolved back to the current Library
`Game` objects by `LibraryService`.

Persisted members whose ROMs are no longer in the current Library
are ignored safely rather than converted into stale launchable
objects.

Games without ROM identities cannot be persisted or launched from
collections.

### Shared Game Details and Launch Path

Playlists reuses the established `GameDetails` component.

Playlist launches therefore continue through the existing:

`CoreResolver`
→ `LaunchValidator`
→ `RetroArchLauncher`

No second playlist-specific launch implementation was introduced.

The reusable Game Details selection state now guarantees:

- Launch begins disabled with no selected game
- Favorite and collection actions begin disabled
- ROM-less games remain non-launchable
- changing to an empty collection clears stale details
- removing the selected member clears stale details
- valid selection restores applicable actions

The live Duck Tales 2 launch from Playlists was confirmed
successful.

### Published Checkpoints

- `a10cd10` — add manual collection persistence
- `064d90f` — expose collections through the Library boundary
- `128bccd` — add the Playlists management page
- `eb432e4` — add Library games to manual collections
- `c498ef1` — remove games from manual collections
- `1df4bfe` — add reusable Game Details selection safety
- `827307e` — add Game Details and launch to Playlists

Published implementation checkpoint before documentation closure:

`827307e761894d74f6e6847975193a99dd8c4abf`

### Validation

Dedicated collection closure baseline:

**53 passing tests**

Complete RetroVault regression baseline:

**324 passing tests**

Compile gate:

**GREEN**

Live application verification confirmed:

- collection creation
- collection rename
- guarded collection deletion
- persistent membership
- duplicate prevention
- safe member removal
- full playlist Game Details
- stale-selection clearing
- successful RetroArch launch from Playlists
- clean normal application exit

No genuine collection TODO, FIXME, stub, or unimplemented
production debt was identified during closure.

### Protected RVDB Boundary

Protected RVDB remains unchanged at:

`1e8bb5d19014fbd0db5b99bc4da382064a44a438`

The collection implementation introduces no RVDB schema,
validator, relationship, build, or release change.

RetroVault continues consuming RVDB through the protected service
boundary.

### Closure Decision

RVA1-C.6-A manual named collections is complete.

No additional collection increment is required merely to extend
the milestone numbering.

Potential future enhancements such as collection reordering,
smart collections, export, or richer playlist presentation may
be introduced as new feature work when justified.

### Next Operation

Begin from the clean post-RVA1-C.6-A checkpoint.

Determine the next RetroVault application milestone from the
current production surface while preserving:

1. the protected RVDB consumer boundary
2. the verified Library launch workflow
3. the verified Playlists launch workflow
4. explicit application-owned persistence
5. safe ROM-identity resolution
6. user configuration protection
7. the 324-test regression baseline unless intentionally expanded

---

## RVA1-C.7 — Shader and Mega Bezel Integration

Status:

**COMPLETE**

RVA1-C.7 establishes RetroVault's first production shader,
Mega Bezel, and external shader-pack integration boundary.

The completed work includes:

- local overlay and shader discovery
- recursive shader-package organization
- transactional shader-package moves
- complete-package dependency handling
- recursive shader preset discovery
- shader browser integration
- guarded shader organization UI
- canonical Mega Bezel layout planning
- canonical Mega Bezel layout preview
- dependency-aware shader preset validation
- runtime-token and foreign-path handling
- bounded compatibility resolution for known stale references
- official Libretro dependency closure
- HSM Mega Bezel Examples DREZ compatibility repair
- live Mega Bezel runtime validation
- live Orionsangel external-pack runtime validation

### Published Checkpoint Before B.9 / B.10 Closure

The protected RetroVault checkpoint before the final dependency
resolution work is:

`2f70889146a9f17613ceae7b9654c59916dabf03`

Short form:

`2f70889`

Checkpoint message:

`feat: preview canonical Mega Bezel layout`

Local and origin remained at this checkpoint throughout the
B.9 / B.10 implementation and verification until final closure.

### RVA1-C.7-B.9 — Dependency-Aware Shader Validation

`services.shaders.service.ShaderService` now validates shader
preset references with dependency-aware path handling.

The resolver supports:

- normal preset-relative references
- RetroArch shader-root-relative references
- `:/shaders/...` references
- `shaders_slang/...` references
- `Mega_Bezel_Packs/...` references
- root-level shader families such as `blurs/...` and `reshade/...`
- foreign absolute RetroArch shader paths remapped to the local
  canonical shader root
- unique case-insensitive path recovery
- runtime token references such as `$TOKEN$`, which are treated as
  dynamic rather than static missing files
- bounded structural compatibility fallbacks for known historical
  Mega Bezel layout changes

The implementation intentionally avoids broad basename guessing.

Case-insensitive fallback succeeds only when the matching path is
unique.

Ambiguous case-insensitive matches remain unresolved rather than
being guessed.

### Structural Compatibility Resolution

Two bounded compatibility cases were established.

First, historical Mega Bezel Base CRT references using:

`shaders_slang/bezel/Base_CRT_Presets/...`

may resolve to the canonical modern location under:

`shaders_slang/bezel/Mega_Bezel/Presets/Base_CRT_Presets/...`

Second, historical `crt-super-xbr` references using a stale local
`shaders/<name>` subdirectory may resolve to the corresponding
known sibling package location.

These fallbacks are deliberately narrow and apply only to their
known structural contexts.

### RVA1-C.7-B.10 — Installed Dependency Closure

The remaining genuine shader dependency gaps were traced to
runtime assets outside the RetroVault repository.

Official Libretro shader dependencies were installed from the
audited upstream `slang-shaders` revision:

`4812a82f6c9a11cc8b5a7447040a98c9fc80c00e`

The installed recursive dependency closure contains the required
`blurs`, `reshade`, and shared `include` assets needed by the
installed Mega Bezel presets.

The original missing seed set included:

- `blurs/shaders/royale/blur9x9.slang`
- ReShade Bloom passes
- ReShade Lens Flare passes
- ReShade Lighting Combine

Their recursive include dependencies were installed together so
the shader runtime does not depend on partial package state.

These files are runtime shader assets and are not part of the
RetroVault Git repository.

### HSM Mega Bezel Examples DREZ Compatibility Repair

The installed HSM Mega Bezel Examples pack contained one
historical DREZ reference using the pre-rename Mega Bezel filename:

`MBZ__3__STD__DREZ-480p__GDV.slangp`

Historical Mega Bezel provenance established that DREZ preset
filenames were renamed so the DREZ suffix appears at the end.

The installed HSM preset:

`Presets/Variations/SegaDC-MVC2__STD__DEREZ-480p.slangp`

was therefore repaired to reference the modern target:

`MBZ__3__STD__GDV__DREZ-480p.slangp`

The repair was constrained to that exact installed preset
reference.

No broad resolver alias was introduced.

The repaired HSM asset is runtime installation state outside the
RetroVault repository.

### Canonical Runtime Layout

The validated runtime shader layout includes:

`shaders_slang/bezel/Mega_Bezel`

`Mega_Bezel_Packs/HSM_Mega_Bezel_Examples`

`Mega_Bezel_Packs/Orionsangel-Original-Console-main`

The protected staging tree remains at:

`orions_angel`

and was not modified by the dependency closure, compatibility
repair, browser experiment, or live runtime testing.

Known protected staging fingerprint:

`87ad50b2e2c4a7265c0e00b3db94f9caa660601d38bd0f044929caac5a74d494`

### Static Dependency Validation

Final installed shader audit:

**1412 installed presets**

**1412 ready presets**

**0 presets with static misses**

**0 unique static misses**

The original structural false-miss cases and genuine dependency
gaps were therefore fully resolved.

### Automated Regression Baseline

Dedicated shader service regression:

**25 passing tests**

Complete RetroVault regression baseline:

**436 passing tests**

Compile gate:

**GREEN**

The final repository verification also confirmed:

- exact expected B.9 implementation/test file set
- clean `git diff --check`
- canonical Mega Bezel assets present
- official Libretro dependency seed files present
- HSM stale DREZ reference absent
- repaired HSM DREZ reference present exactly once
- temporary RetroArch browser symlink absent
- protected staging fingerprint unchanged

### Live Mega Bezel Runtime Validation

The Mega Bezel engine was tested directly through RetroArch using
the verified Duck Tales 2 NES runtime path.

A standard Mega Bezel preset loaded successfully and rendered:

- the game inside the Mega Bezel presentation
- blurred glass treatment
- CRT-style rendering
- surrounding background treatment

The game remained playable at normal speed.

No shader loading or compilation error was observed.

### Live Orionsangel Runtime Validation

The Orionsangel external pack contains a complete Nintendo NES
preset family.

The validated NES Standard preset is:

`Presets/Standard/Nintendo_NES/Nintendo_NES-[STD].slangp`

RetroArch's normal shader browser did not expose the external
`Mega_Bezel_Packs` directory through a temporary symlink placed
under `shaders_slang`.

The temporary symlink was removed after the browser experiment.

The canonical Orionsangel preset was then loaded directly with
RetroArch's `--set-shader` option while launching the verified
Duck Tales 2 ROM through the FCEUmm core.

The live result confirmed:

- Orionsangel artwork rendered correctly
- the game appeared inside the Nintendo console/bezel presentation
- CRT and glass effects rendered correctly
- the complete Mega Bezel dependency chain loaded successfully
- no runtime shader errors were observed
- game speed remained normal

This validates the external Orionsangel pack without relocating,
duplicating, or rewriting its canonical directory structure.

### Runtime Asset Boundary

Mega Bezel, HSM Mega Bezel Examples, Orionsangel, Libretro shader
dependencies, and the repaired installed HSM preset are runtime
assets under the RetroArch shader installation.

They are not application source files and are not committed to
the RetroVault repository by this milestone.

RetroVault source control contains only the application-side
resolver behavior, tests, documentation, and related production
integration work.

### Protected RVDB Boundary

Protected RVDB remains unchanged at:

`1e8bb5d19014fbd0db5b99bc4da382064a44a438`

RVA1-C.7 introduces no RVDB schema, relationship, validator,
build, or release changes.

RetroVault continues to consume RVDB through the established
protected service boundary.

### Closure Decision

RVA1-C.7 shader and Mega Bezel integration is complete.

The final B.9 / B.10 work establishes both:

1. static dependency correctness across the installed shader
   preset population
2. live RetroArch rendering proof through Mega Bezel and the
   Orionsangel external pack

No further shader dependency remediation is required for this
milestone.

Future work may build application-level preset assignment,
per-system shader selection, automatic launch-time shader
application, pack management, or richer presentation features on
top of this validated runtime boundary.

### Next Operation

Begin from the published RVA1-C.7 closure checkpoint after the
final atomic commit and push.

Preserve:

1. the protected RVDB consumer boundary
2. the canonical shader runtime layout
3. the protected `orions_angel` staging tree
4. dependency-aware preset validation
5. the verified RetroArch launch workflow
6. the verified Mega Bezel runtime workflow
7. the verified external-pack runtime workflow
8. the 436-test regression baseline unless intentionally expanded

## RVA1-C.8-B.8 — Production RVV Live Proof

Status:

**COMPLETE**

RVA1-C.8-B.8 established the first complete production
end-to-end proof of the RetroVault Visuals/Presentation
Engine (RVV) overlay path.

The verified production game was:

`Duck Tales 2 (U)`

ROM:

`/home/oilcan/roms/Starter Suite Roms/Nintendo Entertainment System/Duck Tales 2 (U).nes`

A real game-specific presentation assignment was created
through the production RetroVault Overlays page and persisted
in:

`~/.config/retrovault/presentation-state.json`

The assignment resolved to:

`/opt/retropie/configs/all/retroarch/overlays/RetroVault_DuckTales_2_USA.cfg`

The descriptor referenced the verified Duck Tales 2 overlay
artwork.

The normal RetroVault Game Details `Launch Game` action was
then used for the final controlled production proof.

The verified runtime chain was:

`PresentationStore`
→ `PresentationResolver`
→ `LaunchProfile.overlay`
→ `RetroArchLauncher`
→ `OverlayRuntimeConfig`
→ RetroArch append configuration
→ production overlay descriptor
→ Duck Tales 2 artwork

The captured RetroArch runtime configuration contained:

`input_overlay = "/opt/retropie/configs/all/retroarch/overlays/RetroVault_DuckTales_2_USA.cfg"`

and:

`input_overlay_enable = "true"`

The production descriptor referenced:

`/home/oilcan/.var/app/org.libretro.RetroArch/config/retroarch/overlays/Nintendo/NES/NES_DuckTales 2 (USA).png`

Final live confirmation from the single normal production
launch:

- RetroArch opened: YES
- Duck Tales 2 started automatically: YES
- RVV overlay visible: YES
- gameplay responsive: YES
- audio normal: YES

The final production path therefore proved:

`RetroVault UI assignment`
→ persistent RVV state
→ presentation resolution
→ launch-profile injection
→ transient RetroArch configuration
→ overlay descriptor
→ artwork
→ RetroArch
→ automatically launched game with visible overlay

No source workaround was required.

The earlier preliminary launch ambiguity was not reproduced
during the final controlled production launch.

The final B.8 focused regression passed with 79 tests.

B.8 therefore closes with the first verified production RVV
overlay assignment and launch pipeline operating end to end.

## RVA1-C.8-B.9 — Production RVV Shader + Overlay Composition

Status:

**COMPLETE**

RVA1-C.8-B.9 establishes the first production RetroVault
Visuals / Presentation Engine launch in which a persisted
game-specific shader assignment and a persisted game-specific
overlay assignment are resolved and applied together through
the normal RetroVault launch path.

### Production Proof Target

Game:

- `Duck Tales 2 (U)`

ROM:

- `/home/oilcan/roms/Starter Suite Roms/Nintendo Entertainment System/Duck Tales 2 (U).nes`

Core:

- FCEUmm
- `/opt/retropie/libretrocores/lr-fceumm/fceumm_libretro.so`

### Production Shader Assignment

The RetroVault Shaders page assigned the following ready
preset at game scope:

- `/opt/retropie/configs/all/retroarch/shaders/Mega_Bezel_Packs/Orionsangel-Original-Console-main/Presets/Standard/Nintendo_NES/Nintendo_NES-[STD].slangp`

Production ShaderService validation established:

- preset type: `Slang`
- missing dependencies: `0`
- readiness: `True`

The assignment was persisted through PresentationStore using
the canonical Duck Tales 2 game identity.

### Existing Production Overlay Assignment

The B.8 production overlay assignment remained intact:

- `/opt/retropie/configs/all/retroarch/overlays/RetroVault_DuckTales_2_USA.cfg`

The shader assignment did not replace or alter the existing
overlay assignment.

### Presentation Resolution

PresentationResolver returned both presentation fields
simultaneously for Duck Tales 2:

- shader: Nintendo NES `[STD]`
- overlay: `RetroVault_DuckTales_2_USA.cfg`

This confirms that presentation-field precedence and merging
operate independently and preserve shader + overlay
composition.

### Normal Production Launch Proof

Duck Tales 2 was launched through the normal RetroVault UI:

`Library`
→ `Game Details`
→ `Launch Game`
→ `PresentationStore`
→ `PresentationResolver`
→ `LaunchProfile`
→ `RetroArchLauncher`
→ `RetroArch`

The live RetroArch command contained:

- FCEUmm core
- Duck Tales 2 ROM
- `--appendconfig`
- transient OverlayRuntimeConfig path
- `--set-shader`
- exact Nintendo NES `[STD]` preset

### Atomic Runtime Evidence

The controlled live proof captured the active RetroArch command
while RetroArch was running and copied the transient overlay
runtime configuration before cleanup.

Validation confirmed:

- exact Duck Tales 2 ROM
- exact FCEUmm core
- exact Nintendo NES `[STD]` shader through `--set-shader`
- overlay injection through `--appendconfig`
- exact RetroVault Duck Tales 2 overlay descriptor
- overlay runtime enabled

### Live Production Validation

The combined shader + overlay production launch passed all
manual runtime checks:

- RetroArch opened
- Duck Tales 2 started automatically
- Duck Tales overlay was visible
- Nintendo NES / Orionsangel shader was visible
- gameplay was responsive
- audio was normal

### Automatic End-to-End Production Launch

A final external test harness initialized the real RetroVault
application without modifying production source.

The harness used the actual `LibraryPage.all_games` collection,
located exactly one real Duck Tales 2 game object, passed that
object to the production `GameDetails.show_game()` method, and
then invoked the existing production
`GameDetails.launch_game()` method automatically.

Terminal proof established:

- exactly one Duck Tales 2 production library object matched
- the real game object was selected automatically
- launch validation returned `Game is ready to launch.`
- the production launch method was invoked
- no manual Launch Game click was required

Live user validation established:

- RetroVault opened normally
- zero manual launch clicks were made
- RetroArch opened automatically
- Duck Tales 2 started automatically
- the Duck Tales overlay was active
- the Nintendo NES shader was active
- gameplay and audio were normal

This test demonstrates that the existing RetroVault production
architecture can support automatic game launching while still
using the normal presentation-resolution and launch pipeline.

It does not add an automatic-launch feature to RetroVault;
the harness existed only as an external production proof.

### Regression Proof

B.9 regression checkpoints passed:

- baseline focused regression: 84 passed
- assignment recovery regression: 59 passed
- final focused production regression: 81 passed

### Protection Results

B.9 required no RetroVault production source workaround.

Throughout the production proof:

- RetroVault source remained unchanged
- local and GitHub protected checkpoints remained unchanged
- protected RVDB remained unchanged
- protected C.7 Orionsangel staging remained unchanged
- the B.8 overlay assignment remained preserved
- the B.9 shader assignment remained persisted

### B.9 Closure

RVA1-C.8-B.9 is complete.

RetroVault has now demonstrated simultaneous production RVV
shader + overlay composition through the real launch pipeline,
including successful automatic end-to-end invocation using the
existing production game object and launch method.

## RVA1-C.8 — RetroVault Visuals / Presentation Engine Foundation Closure

Status:

**COMPLETE**

RVA1-C.8 establishes the application foundation for the
RetroVault Visuals / Presentation Engine (RVV).

The milestone now provides a production-capable presentation
architecture spanning discovery, validation, persistence,
resolution, assignment, and launch-time application of
RetroArch presentation assets.

### Foundation Capabilities Established

The completed RVV foundation includes:

- local shader discovery and validation
- local overlay discovery and validation
- canonical Mega Bezel package integration
- shader dependency validation
- persistent presentation state
- independent shader and overlay assignment
- Default, System, and Game presentation scopes
- presentation precedence resolution
- launch-time shader injection
- launch-time overlay configuration
- RetroVault Shaders page assignment controls
- RetroVault Overlays page assignment controls
- production RetroArch launch integration

### Presentation Architecture

The production presentation boundary is composed of:

`PresentationStore`
→ `PresentationResolver`
→ `LaunchProfile`
→ `RetroArchLauncher`

Presentation state supports independent shader and overlay
fields so each property can resolve through its own
Game > System > Default precedence chain.

### Production Proof

Duck Tales 2 (U) provided the controlled production target.

The final production proof demonstrated simultaneous use of:

- FCEUmm
- Duck Tales 2 (U)
- Nintendo NES `[STD]` Orionsangel shader
- RetroVault Duck Tales 2 overlay

The normal RetroVault launch path successfully resolved both
presentation fields and supplied them to RetroArch together.

Runtime proof confirmed:

- `--set-shader` received the exact assigned shader
- `--appendconfig` received the transient overlay configuration
- the overlay runtime descriptor was enabled
- the expected game overlay was visible
- the expected shader was visible
- gameplay remained responsive
- audio remained normal

### Automatic Production Invocation Proof

A temporary external verification harness also initialized the
real RetroVault application, located the actual Duck Tales 2
library object, selected it through the production Game Details
surface, and invoked the existing production launch method
without a manual Launch Game click.

This proved that automatic launch intent can drive the existing
RVV pipeline without bypassing presentation resolution or the
normal RetroArch launch architecture.

No permanent auto-launch feature was added during RVA1-C.8.

### Closure Audit

The final closure audit verified:

- production presentation models exist
- production PresentationStore exists
- production PresentationResolver exists
- shader assignment APIs exist at Default/System/Game scope
- overlay assignment APIs exist at Default/System/Game scope
- resolved shader and overlay fields reach LaunchProfile
- RetroArchLauncher applies both presentation mechanisms
- no genuine RVV production TODO/FIXME/NotImplemented/pass debt remains

The two bare `pass` statements identified during audit were
confirmed to be test scaffolding only:

- ReadyValidator test-double constructor
- FakeResolver test-double class

They do not represent production implementation debt.

### Protection Results

Throughout RVA1-C.8:

- the protected RVDB consumer boundary remained intact
- RVDB remained unchanged
- the protected C.7 shader staging state remained intact
- production proofs required no source workaround
- runtime presentation state remained separate from Git source
- milestone work remained regression-gated and checkpointed

### RVA1-C.8 Closure

RVA1-C.8 is complete.

RetroVault now has a verified production foundation for the
RetroVault Visuals / Presentation Engine.

Future RVV work can build on this boundary with richer asset
management, broader system/game coverage, automated presentation
selection, curated RetroVault visual packs, and higher-level
presentation workflows without reopening the foundational
launch architecture established here.

## RVA1-C.4-A.4b — First Native RVV Visual Production Closure

Status:

PRODUCTION COMPLETE

RetroVault now contains its first original native
RetroVault Visuals / Presentation Engine (RVV)
production visual:

`Nintendo NES — RetroVault Classic`

Production identity:

- visual ID: `rvv.overlay.nes.classic`
- family: `RetroVault Classic`
- platform: `platform.nintendo.nes`
- asset type: `overlay`
- source: `rvv_native`
- author: `RetroVault`
- production status: `production`

The approved native visual is stored as a portable
RetroArch overlay package:

- `retrovault/nes/classic/RetroVault_NES_Classic_1080p.png`
- `retrovault/nes/classic/RetroVault_NES_Classic.cfg`
- `retrovault/nes/classic/RetroVault_NES_Classic.production.json`

The production PNG uses a 1920x1080 RGBA canvas with
one exact transparent gameplay aperture:

- x: 355
- y: 100
- width: 1188
- height: 751

The gameplay aperture is presentation geometry only.
NES gameplay remains independently controlled as 4:3
by RetroArch and the active shader/presentation
pipeline.

The approved production visual preserves the native
RVV design language established during C.4-A:

- premium showroom / restored-hardware presentation
- clean NES-inspired industrial character
- gameplay-dominant composition
- RetroVault as primary presentation identity
- RetroVault branding centered below gameplay with
  restrained red accent lines
- Nintendo platform identity centered beneath
  RetroVault without flanking red lines
- maintained POWER and RESET controls with restrained
  functional wear
- exceptionally crisp and aligned presentation
  branding

Originality and provenance remain explicitly bounded:

- the bezel composition, frame treatment, layout,
  materials, RetroVault branding, and presentation
  design are original RetroVault work
- no third-party bezel artwork, console photography,
  or external visual-pack artwork is incorporated
- third-party platform names and trademarks remain
  the property of their respective owners
- RetroVault does not claim ownership of Nintendo
  platform identification

The production asset was deployed through the actual
configured RetroArch overlay root and resolved through
the normal RetroVault portable presentation reference:

`retro-vault://overlays/retrovault/nes/classic/RetroVault_NES_Classic.cfg`

The native overlay was then selected through
RetroVault's normal presentation state and composed
with the existing Nintendo NES Orionsangel `[STD]`
shader through the production application path.

The controlled live proof used the temporary
`Duck Tales 2 (U)` NES validation game.

Live acceptance confirmed:

- game launched successfully through RetroVault
- FCEUmm operated through the configured application
  core boundary
- native RetroVault NES Classic bezel was visible
- gameplay appeared correctly through the transparent
  aperture
- Orionsangel Nintendo NES `[STD]` shader was visible
- RetroVault and platform branding were correctly
  positioned
- bezel/game alignment was correct
- controls operated normally
- audio operated normally

The temporary presentation assignment was restored
after the proof and repository state remained
unchanged by the runtime validation.

The production visual is registered in:

`data/presentation/visual_catalog.json`

The catalog entry is loaded through the typed
`VisualAssetCatalogManifest` boundary and preserves
the portable overlay reference.

The approved production artifacts are locked by the
following SHA-256 values:

- CFG:
  `8ed0e8f5828e65c573bca87a4537705e791d17fe54b40d422b7acb626438a3f2`
- production metadata:
  `68732c989666f53f1ddc5d0e485d4b76bb1b274e64c60ad59bb922147b5b2694`
- PNG:
  `991f4f67999a3d466025d597cdce662b396b3ccfecf2b754a6c68c18f5fb4d05`

This closes the first complete native RVV production
asset lifecycle:

specification
→ approved master design
→ production geometry
→ deterministic transparent aperture
→ portable RetroArch descriptor
→ runtime deployment
→ RetroVault portable-reference resolution
→ application-path live proof
→ human visual acceptance
→ production promotion
→ typed visual-catalog registration

The first native RVV visual therefore establishes the
production pattern that later RetroVault system and
game visual families can follow without reopening the
RVV launch architecture.

Temporary proof content, including the Duck Tales 2
validation game and earlier development visual debris,
remains outside the native production visual contract
and may be cleaned up independently.
## RVA1-C.4-B — Native RVV Visual Selection and Deployment Foundation

Status:

COMPLETE

RetroVault Visuals / Presentation Engine (RVV) now has a
production-grade native visual deployment boundary for cataloged
RetroVault-owned overlay packages.

### C.4-B.1 — Architecture Audit

The native visual selection and deployment audit confirmed that the
existing RVV architecture already provided the required metadata,
portable-reference, presentation-assignment, and runtime composition
boundaries.

The existing visual catalog remains authoritative for:

- visual identity
- asset type
- ownership/source classification
- portable references
- author and attribution metadata

No parallel visual database or alternate catalog architecture was
introduced.

Deployment and presentation assignment remain separate operations.

### C.4-B.2 / C.4-B.2a — Native Deployment Contract

`NativeVisualDeploymentService` establishes the filesystem deployment
boundary for cataloged RVV-native overlays.

The catalog-relative path is authoritative for both locations:

repository root + catalog-relative path

→ configured RetroArch overlay root + catalog-relative path

For the first native production visual:

`retro-vault://overlays/retrovault/nes/classic/RetroVault_NES_Classic.cfg`

maps from:

`retrovault/nes/classic/RetroVault_NES_Classic.cfg`

to the same `retrovault/nes/classic/...` namespace beneath the
configured RetroArch overlay root.

The deployment layer rejects:

- non-RVV-native assets
- unsupported visual asset types
- non-portable overlay references
- unsafe relative paths
- source paths escaping the native production package root
- overlay image references escaping their production package
- destinations escaping the configured overlay root

### C.4-B.3 / C.4-B.3a — Transactional Package Deployment

Native RVV package installation is transactional at the package
directory boundary.

The deployment process:

1. creates a staging package beside the final destination;
2. copies every authoritative production file into staging;
3. verifies staged bytes against the source package;
4. moves an existing installed package to a temporary backup;
5. atomically replaces the destination with the completed staged
   package;
6. restores the previous package if final replacement fails;
7. removes obsolete files by replacing the complete package rather
   than merging file-by-file;
8. removes staging and backup transaction debris after success.

Planning remains read-only.

Presentation assignment, recommendation precedence, generic overlay
discovery, and RetroArch launch behavior remain outside this
deployment boundary.

### C.4-B.4 — Configured Native RVV Application Service

`NativeVisualService` provides the application-facing boundary above
native deployment.

It consumes the existing RetroVault configuration system through
`ConfigLoader` and the existing visual catalog through
`VisualAssetCatalogManifest`.

The service exposes three installation states:

- `NOT_INSTALLED`
- `CURRENT`
- `OUTDATED`

`CURRENT` requires the deployed package to match the authoritative
production package exactly.

Missing files, changed bytes, or unexpected files cause an installed
package to report `OUTDATED`.

Installation is explicit. Merely querying status or browsing the
catalog does not deploy files and does not alter presentation
assignments.

Effective configuration is reloaded for operations so a user change
to the configured overlay directory can be honored without introducing
a second path configuration mechanism.

### C.4-B.5 — Production-Path Proof

The configured application service was exercised against the real
RetroVault environment.

Verified production chain:

RetroVault `ConfigLoader`

→ RVV visual catalog

→ `NativeVisualService`

→ `NativeVisualDeploymentService`

→ configured RetroArch overlay root

→ portable RVV reference resolution

The effective overlay root resolved to the live RetroArch overlay
location.

The production asset:

`rvv.overlay.nes.classic`

resolved to:

`Nintendo NES — RetroVault Classic`

and reported `CURRENT` before the live proof installation.

A live transactional reinstall completed successfully and remained
`CURRENT`.

The deployed CFG and PNG were byte-identical to the locked production
source files.

The portable RVV reference resolved to the exact deployed descriptor.

No staging or backup transaction debris remained.

The proof did not modify:

- the RVV visual catalog
- presentation assignments
- recommendation precedence
- RetroArch launch behavior
- user configuration
- the locked production NES visual
- unrelated repository files

### C.4-B Closure Contract

Native RVV visual deployment is now an application service rather than
a UI or launch-time filesystem concern.

The protected boundary is:

User-facing RVV selection

→ native visual application service

→ effective RetroVault configuration + visual catalog

→ transactional native deployment

→ configured RetroArch visual root

Presentation selection and assignment remain an independent layer.

This allows future system-level and game-level native RVV visual
collections to reuse the same deployment infrastructure without
reopening the RetroArch launch architecture.

### C.4-B Validation

Closure validation includes:

- dedicated native deployment tests
- dedicated configured native-service tests
- configuration regression
- presentation regression
- full RetroVault regression
- repository scope validation
- production NES checksum lock validation
- real configured-path deployment proof
- source/deployed byte-identity proof
- portable-reference resolution proof
- transaction cleanup proof

No user-facing RVV selection UI is included in C.4-B.

Next milestone:

RVA1-C.4-C — User-Facing RVV Visual Selection.

## RVA1-C.4-C — User-Facing RVV Visual Selection

Status:

CLOSED

Closure establishes the first production user-facing
RetroVault Visuals collection surface.

Implemented application surface:

- dedicated `RetroVault Visuals` page
- separate from the existing installed-filesystem
  `Overlays` browser
- catalog-driven native RVV visual discovery
- no duplicate or parallel visual catalog
- no native-asset filesystem scanning from the UI
- installation state supplied by `NativeVisualService`
- authoritative production-package preview
- explicit install/update action only
- no automatic installation on selection
- no automatic presentation assignment on installation
- existing presentation assignment precedence unchanged
- existing launch architecture unchanged

First production collection entry:

- ID: `rvv.overlay.nes.classic`
- Display name: `Nintendo NES — RetroVault Classic`
- Source: `rvv_native`
- Type: `overlay`
- Author: `RetroVault`
- Production installation state: `current`

Navigation integration:

- `RetroVault Visuals` registered in `MainWindow`
- sidebar entry registered explicitly
- sidebar placement between `Overlays` and `Shaders`
- navigation opens the dedicated native RVV page
- UI shell regression updated for the new navigation entry

Live human acceptance:

PASS

Confirmed in the production application:

- `RetroVault Visuals` physically appears in the sidebar
- navigation opens the correct page
- `Nintendo NES — RetroVault Classic` is listed
- production NES bezel preview is visible
- visual metadata is correct
- installation state displays `Installed`
- Installed button is disabled while the package is current
- page layout is visually acceptable

This closure establishes curated browsing, preview,
production installation status, and explicit deployment
management for native RetroVault visuals.

Default/system/game presentation assignment is intentionally
not introduced by this milestone. Assignment remains behind
the existing `PresentationStore` boundary for subsequent
controlled integration.

No recommendation precedence changes were made.

No launch architecture changes were made.

No parallel catalog, configuration, or assignment
architecture was introduced.
