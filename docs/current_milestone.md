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
