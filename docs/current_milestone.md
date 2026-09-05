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
