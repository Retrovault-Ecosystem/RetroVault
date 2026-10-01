# Milestone #11 — Metadata/artwork

The approved offline metadata/local-cover scope is implemented using the existing
RVDB, Library and presentation architecture. No replacement database, service,
network provider or persistence schema was introduced.

## Metadata contract

RVDBService and RVDBGameSummary remain the canonical knowledge boundary.
RVDBLibraryResolver deduplicates equivalent title/platform aliases by entity ID.
Exact game title/alias matches within a canonical platform retain priority, and
ambiguous exact results never fall through to a guessed alternative.

RomScanner uses the resolver's conservative ROM-name fallback. Existing
VariantClassifier semantics identify retail region/revision tags; bracketed dump
flags, hacks, translations, prototypes, demos and unlicensed variants are not
silently identified as the original retail title. Unknown tags remain part of the
title. A fallback still requires a unique existing RVDB game on the same platform.
No metadata is invented, and matching does not change the ROM path or local ID.

The installed bundle still contains four canonical games. The three live runtime
qualification titles are not among them. Missing years/descriptions/game matches
remain absent; this milestone is not a catalog population or scraping operation.

## Local-cover contract

ArtworkService remains the local Library cover owner. It uses the configured root
and existing PNG/JPEG/WebP support, recognizes canonical platform IDs, names and
aliases supplied by RVDBLibraryResolver, and excludes recognized foreign or
conflicting platform folders. Unique unscoped legacy covers remain supported.

Precedence is an existing explicit file, then exact ROM-stem discovery, then a
unique canonical-title cover for an already identified RVDB game. Ambiguous exact
candidates do not silently fall through to canonical-title artwork. Within a title,
a unique matching platform-scoped file takes precedence over unscoped candidates.
No file-extension or artwork-category preference silently resolves duplicates.

Game.artwork remains the display path. Two additive in-memory fields,
artwork_origin and artwork_explicit, distinguish discovered results from supplied
paths and retain explicit intent if its file temporarily disappears. No durable
assignment editor or store is added. Cache entries include canonical identity and
are checked for file existence; explicit refresh/reload invalidates the index.

LibraryService refreshes physical editions and rebuilds their visible family
projection. Canonical variant records carry each edition's cover provenance, so
reconstruction does not copy a representative's cover onto a different edition.
MainWindow refreshes Library and Playlists after an artwork-directory change.
GameDetails and GameCard render metadata/title text literally and retain existing
aspect-preserving image display and invalid/missing-image placeholders.

## Ownership boundaries

- RVDB: canonical facts; no local paths or user state.
- Library: local files, canonical enrichment, edition grouping and derived covers.
- Persistence: existing IdentityRegistry, LibraryState, CollectionStore and
  PresentationStore retain authority. Formats and local identities are unchanged.
- Presentation: Library covers do not become PresentationProfile.artwork, overlay
  or shader preferences. Production-package authority remains unchanged.
- Runtime configuration: no viewport, overlay, shader or session-builder changes.
- Execution: no core policy, launch prerequisites, process ownership or emulator changes.

## Verification

Full automated suite: **2,142 passed** (`build/milestone11/automated-tests.log`).
The new `tests/test_metadata_artwork_pipeline.py` covers safe matching, duplicate
aliases, ambiguity, foreign platform covers, canonical fallback, stale files,
explicit precedence/restoration, edition refresh and canonical cache isolation.
A separate interpreter reconstructs scanned metadata/artwork and verifies exact
local identity, favorite, collection, history and saved overlay preservation.
Existing platform-pipeline tests continue exercising NES, SNES and Genesis
launch/presentation boundaries with isolated runtime doubles.

Offscreen UI review: `build/milestone11/ui-review.png`, using a clearly labeled
synthetic cover. Card/details covers preserve aspect ratio; metadata is legible and
markup-like text is displayed literally. This is an implementation review, not a
claim of user acceptance of new cover art or a new live emulator qualification.
No launch behavior changed, so a new live gameplay run was not required.

The configured local artwork directory was absent during inspection. Place owned
local cover files in the configured root, preferably under the canonical platform
ID or an RVDB platform name/alias, then refresh the Library. Actual missing covers
continue to show placeholders. Artwork file format support does not guarantee a
file is a decodable image; Qt retains its safe placeholder behavior.

## Scope and completion

No changes to RVDB sources/bundles, approved NES/SNES/Genesis artwork or shaders,
core/readiness policy, user-state formats or emulator execution. No online scraping,
downloads, metadata editor, persistent manual assignments, description-schema
extension, new cover generation or new platforms.

**Milestone #11 is complete and formally closed within the approved scope.**

Final closure audit confirmed the passing 2,142-test full suite, 196 focused checks,
fresh-process persistence verification and isolated UI review. Diff integrity checks
passed. No approved implementation or verification work remains. The user requested
formal closure: "Finish up and then close milestone 11". This does not imply new
user visual acceptance, downloaded covers, a commit or a release.

Milestone #12 has not started.
