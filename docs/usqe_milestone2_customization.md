# USQE Milestone #2 — Reversible customization, first usable slice

Status: **complete following user approval of the implementation report and final closure.**
**USQE #3–#12 remain unstarted.**
The original 14-milestone roadmap and USQE #1 decision baseline remain closed and protected.

## Authorization and protected starting points

The user approved the read-only implementation plan with Small/Large dimensions as
implementation candidates, subject to bounded Bring It to Life review. Default stays protected.

- RetroVault: `feature/rvdb-foundation`, `4bcfa25110cb4af39b4be5942e27ba53d71cbe9a`.
- RVDB: `develop`, `871b7f8b467db2ff22e6dbd994cef6af0d6a8d44`.
- Both worktrees started clean and local heads matched their remote branches.
- RVDB requires no changes. No emulator launch is part of this milestone.

## Implemented contract

Application configuration owns three symbolic preferences, under `library.display`:

| Field | Default | Values |
| --- | --- | --- |
| `opening_view` | `gallery` | `gallery`, `details`, `compact` |
| `card_size` | `default` | `small`, `default`, `large` |
| `normal_sort` | `name` | `name`, `year` |

`config/library_preferences.py` provides the small Qt-independent contract. ConfigLoader
normalizes invalid/obsolete display values per field, or defaults an invalid subsection,
without writing. Absent keys need no migration. Submitted values are strictly validated.
Unrelated configuration errors are not suppressed, and unknown fields remain preserved.

SettingsService saves only the display override through the existing ConfigWriter. It uses
the existing saved/refresh-unavailable result pattern. Settings owns the draft and last
successfully applied baseline; MainWindow connects its preview/applied signals to Library.

- Preview updates the existing Library in memory, without writing or rescanning.
- Apply validates, writes atomically, adopts the written baseline and reasserts it in Library.
- Cancel restores applied preferences, preserving unrelated selection/search/filter actions.
- Reset previews approved defaults and requires Apply to persist.
- Failed write keeps previous bytes and the applied baseline; preview stays explicitly unsaved.
- Successful write/failed reread is saved with a warning, not falsely reported as a failed save.
- App exit discards unsaved drafts. Fresh startup restores applied values.
- Ordinary Library view/sort clicks remain session-only; they do not mutate Settings drafts.
- Opening Settings or refreshing unrelated Settings controls does not erase the draft.

## Library behavior and compatibility

Gallery/Details/Compact reuse the existing stack; programmatic changes synchronize selector
labels/checks. Initial Name preference deliberately retains service ordering until ordinary
refresh, matching the protected baseline. Explicit Year sorts at startup. Existing Name
comparison and Year ordering (unknown years first, stable ties) remain unchanged.

Recently Played still uses history order. Search/system/favorites filters retain their
semantics. Collection/playlist ownership and ordering are unchanged.

Preference-driven sort rebuilds preserve selected game identity and shared details, block
spurious list-selection signals, restore applicable row selection, and restore/clamp scroll
positions. Cancel does not revert a different game or filter the user intentionally selected.

Card-only changes update existing widgets and retain game objects/click connections. Artwork
rescales from its source, not a previously scaled image. Startup constructs cards using the
selected size immediately. Symbolic preferences can be consumed by a later renderer without
pre-building virtualization or moving pixels into persistent configuration.

## Bring It to Life review

The bounded agent review used synthetic Qt/offscreen fixtures and the existing application
theme. It is not a claim of user live acceptance, emulator qualification or all-display testing.

| Choice | Card width | Artwork area | Review outcome |
| --- | ---: | ---: | --- |
| Small | 170 px | 140×175 px | Retained after bounded review and user approval of the final report. |
| Default | 190 px | 160×200 px | Protected; four representative card images pixel-identical to baseline. |
| Large | 230 px | 200×250 px | Retained after bounded review and user approval of the final report. |

Reviewed long names, missing/invalid artwork, wide/tall artwork, edition badges, narrow/wide
views, scrolling, Settings labels/status controls and the established palette. Automated Qt
keyboard checks exercise dropdown navigation and tab focus. No candidate dimensions changed.

The existing renderer center-clips very long Default titles; that protected rendering remains
unchanged. Small/Large instead use an ellipsis with a full-name tooltip. This is confined to
the candidate card choices. New Settings group/actions reuse existing Settings style roles;
no theme file or unrelated layout changed.

Five columns remain at all widths. Narrow views require horizontal scrolling; the review
verified access to the last columns and bottom rows. Wide views retain top-left packing.
This is an intentional preserved limit, not responsive-grid or Milestone #4 work.

Review artifacts and test logs were generated under `/tmp/usqe2-visual-review` and
`/tmp/usqe2-verification`; they are local session evidence, not committed production assets.
The temporary logs/screenshots were no longer available at the closure resumption; the results above are the previously completed verification, not newly rerun tests. Representative fixture coverage is durable in the new tests.

## Verification

New regressions were added before/alongside implementation and reproduced absent preference,
preview and startup-construction behavior before their corresponding fixes.

- New preference and Qt integration cases: 57.
- Final focused batch: 282 passed (new cases plus affected existing config/settings,
  Gallery/artwork, refresh/source reload, MainWindow synchronization and boundary tests).
- Final full RetroVault suite: **2,270 passed in 52.75 seconds** after the final production adjustment.
- Syntax compilation and AST parsing: 329 Python files passed.
- Fresh imports: all 13 changed production modules passed.
- Atomic save failure injections: serialization, partial write, flush, fsync and replacement;
  old bytes intact and temporary files removed in every case.
- Real MainWindow composition: preview wiring, navigation, Apply and fresh-window restoration
  exercised using isolated roots and empty sources, without launching an emulator.
- Selection/scroll, session-only choices, repeated Cancel, reset/apply/restart, safe fallback,
  unrelated key preservation and successful-write/failed-reread covered.
- Existing complete suite covers collections, import/canonicalization, startup, architecture,
  presentation authority and runtime/lifecycle regressions.

All verification uses synthetic/disposable fixtures and isolated configuration/state/cache
where application composition is involved. RVDB tests are not repeated because RVDB is unchanged.

## File boundary and protected surfaces

Production edits are limited to the 12 existing files approved in the plan plus the new
`config/library_preferences.py`. Tests are in `tests/test_library_preferences.py` and
`tests/test_library_preferences_integration.py`; existing test assertions are unchanged.
Documentation changes are this record, README, current milestone, configuration/startup guide
and the USQE roadmap's current status. USQE #1 and original historical acceptance files are unchanged.

No RVDB/schema/data, ROM identity/canonicalization, physical edition, favorites/history/
collections persistence, import architecture, PresentationStore, gameplay presentation,
shader/bezel/logo/viewport, production package, emulator configuration, readiness/core,
save/controller or process-lifecycle production file changes.

No arbitrary pixel controls, global theme redesign, responsive grid, virtualization,
background discovery, platform expansion or USQE #3 functionality is included.

## Final approval and closure

The user explicitly approved the completed implementation report and authorized final
documentation closure, commit and normal push. The approved report records 57 new cases,
282 focused checks and 2,270 complete-suite passes. Closure changes only documentation;
production and test code remain the verified implementation.

The closure sequence verifies the exact approved file boundary, whitespace, historical
record preservation and protected starting HEAD; stages files explicitly; commits and
pushes normally; then verifies local/remote equality, zero divergence and a clean worktree.
The resulting commit hash is reported after publication rather than embedded in its own
commit. RVDB remains unchanged. No Milestone #3 work is authorized or started.
