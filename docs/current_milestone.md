# RetroVault Current Milestone

## RVA1-C.12 — Bulk Import Production Workflow

**Status:** COMPLETE / PROTECTED

RVA1-C.12 establishes RetroVault's production Bulk Import workflow
for adding ROM directories to the live application library while
preserving the protected library, RVDB, collection, launch, archive,
RVV, and runtime architecture.

### Bulk Import discovery

RetroVault provides a production Bulk Import service built on the
existing library scanner architecture.

The workflow:

- Accepts a user-selected ROM directory.
- Validates the directory through the existing source-validation
  boundary.
- Uses RetroVault's existing recursive ROM scanner.
- Preserves RVDB resolver integration.
- Deduplicates discovered games by canonical ROM identity.
- Produces deterministic import ordering.
- Ignores unsupported files through the existing scanner contract.
- Rejects invalid or missing source directories.
- Safely supports an empty valid ROM directory.

Bulk Import discovery itself does not directly mutate runtime
configuration or durable library state.

### Production application experience

The Library page exposes Bulk Import through the production toolbar.

A successful import reports:

- ROMs discovered.
- Games added.
- Games already present or skipped.
- Duplicates found inside the selected source.
- Whether the directory was newly saved or was already registered
  as a library source.

Import failures are surfaced through the production Bulk Import
failure path.

Development and coding diagnostics remain separate from intentional
production-facing application feedback.

### Live library integration

A successful Bulk Import is merged into the active RetroVault
library immediately.

The controller returns the authoritative live library snapshot after
the merge.

The Gallery consumes that explicit snapshot rather than relying on
handler ownership or bound-method introspection.

The protected implementation does not use:

- `_bulk_import_games` handler introspection.
- `__self__` handler-owner inspection.

This keeps the Bulk Import boundary explicit and compatible with
wrapped or independently supplied handlers.

### Application synchronization

After a successful import, RetroVault synchronizes dependent
application surfaces.

The Systems page refreshes its live library-derived information for
the current system selection.

The Playlists page refreshes its live collection contents while
preserving the currently selected collection when possible.

The Library page already receives the authoritative post-import
library snapshot.

Bulk Import completion synchronization is not emitted when the
import fails.

### Persistent library sources

Successfully imported directories are stored as enabled local
library sources in RetroVault runtime configuration.

Persistence:

- Preserves existing configured sources.
- Uses canonical source paths.
- Avoids duplicate registration of the same directory.
- Generates unique source IDs when required.
- Uses the existing atomic runtime configuration writer.

A directory that is already registered is reported as an existing
source rather than duplicated.

### Restart rehydration

Persisted Bulk Import sources participate in RetroVault's normal
startup library-loading architecture.

On a subsequent application startup:

- Runtime configuration is merged with default configuration.
- SourceManager reconstructs the persisted local source.
- LibraryService supplies that source to LibraryBuilder.
- The normal scanner architecture rebuilds the imported library.

The restart contract is explicitly regression-tested.

Repeated persistence of the same source does not create duplicate
startup sources.

### Empty-source hardening

A valid empty ROM directory is a supported Bulk Import source.

It produces:

- Zero discovered games.
- Zero duplicate games.
- An empty immutable game result.
- A valid enabled local source identity.

This behavior is protected by regression coverage.

### Protected Bulk Import boundaries

RVA1-C.12 protects:

- Bulk Import discovery and validation.
- Recursive scanner reuse.
- RVDB resolver propagation.
- Canonical ROM identity deduplication.
- Deterministic discovery results.
- Live LibraryService merge behavior.
- Explicit authoritative post-import game snapshots.
- Production success and failure feedback.
- Runtime source persistence.
- Duplicate source prevention.
- Unique source IDs.
- Cross-page application synchronization.
- Restart rehydration.
- Empty-source behavior.

### Preserved earlier architecture

RVA1-C.12 does not alter the protected contracts for:

- RVA1-C.10 launch/session ownership and lifecycle behavior.
- RVA1-C.11 application UX hardening.
- Archive variant selection and archive-member safety.
- RetroArch process ownership and shared-session protection.
- Favorites and Recently Played identity rules.
- Collection identity and persistence.
- RVDB resolver architecture.
- Interactive hardware-state architecture.
- NES protected RVV visual geometry.
- SNES protected RVV visual geometry.

### Closure validation

RVA1-C.12 closure validation established:

- Bulk Import regression: PASS.
- Cross-page regression: PASS.
- Discovery contract: PASS.
- Persistence contract: PASS.
- Live-library integration contract: PASS.
- Gallery refresh contract: PASS.
- Application synchronization contract: PASS.
- Restart rehydration contract: PASS.
- Empty-source hardening contract: PASS.
- Full RetroVault regression: 1185 passed.
- Python compile validation: PASS.
- Local/remote protected branch synchronization: PASS.
- Clean worktree before documentation closure.

### Technical closure checkpoint

RVA1-C.12 technical implementation was validated at:

`886af98de5826ff079630ffc581f5937f626e027`

The final protected milestone checkpoint is the documentation closure
commit that contains this document.

### Next milestone

The next RetroVault milestone begins from the protected RVA1-C.12
closure checkpoint.
