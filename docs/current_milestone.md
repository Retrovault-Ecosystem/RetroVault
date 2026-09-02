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

**READY TO BEGIN**

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
