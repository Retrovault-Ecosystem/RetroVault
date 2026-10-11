# USQE #4 — Large-library browsing and rendering

Status: **complete following user approval of the implementation report and closure.**
Baseline: `0b3ccfa3d6bfbf48accfab32e14aab48439c71c1`. RVDB unchanged.

## Measurement and pre-implementation targets

`scripts/measure_library_rendering.py` measures synthetic in-memory families in the
actual GalleryView, at 1400×800, offscreen Qt 6.11.0 / Python 3.14.4 on Linux x86_64.
Each family has one synthetic identity; no disk ROMs, archives, artwork, overlaps or
additional editions in the initial isolated rendering workload. This separates view
cost from discovery. Three fresh-process repetitions per size; warm OS cache is not
called cold. Larger baseline runs are limited to 30 seconds and 2 GB virtual memory.
Artwork, edition and repeated-operation correctness require separate verification.

The baseline 2,000-family construction median is .859 seconds; 10,000 takes about
5.1 seconds. This establishes that eager widget construction needs bounding.

Before production edits, set these local acceptance targets (not product capacity SLAs):
- 2,000-family construction under .43 seconds (at least twice as fast as baseline).
- 10,000-family construction under 1 second; 50,000 under 2 seconds.
- Search update under .2 seconds for the no-artwork fixture at all four sizes.
- Gallery cards bounded by five columns times visible rows, two buffer rows on each
  side, and at most one partially visible row; no full-library image cache.
- Repeated operations leave no retired cards after deferred deletion and no unbounded
  retained image/widget growth. Record memory rather than asserting allocator RSS returns
  exactly to its initial value.

Approved appearance, five columns, card sizes, identity selection, query ordering,
preferences and M3 discovery/publication contracts remain protected. Actual gameplay,
RVDB, persistence and runtime policies are outside scope. Numerical targets must be
reported honestly, including any missed target; no post-hoc silent relaxation.


## Implementation

GameGrid retains five columns and unchanged GameCard contents, styles, cover proportions
and size choices. Only buffered rows have cards. Overlapping cards survive scrolling;
retired cards/images are released through Qt deferred deletion. Row extents are uniform
and reserve space for edition labels where needed, preventing jumps when the buffered
window changes. This can leave extra row spacing in mixed-edition lists; card appearance
and content remain unchanged.

DetailsView and CompactView share GameListModel/GameListView. Qt requests display text
on demand instead of allocating a QListWidgetItem per game in both hidden views. Models
still retain references to the complete filtered result; this is not constant-memory
inventory. Gallery restores selected identity around model resets. Query computation
remains synchronous and measured within target, so no worker/debounce framework was added.

No changes were necessary to discovery workers, state publication, artwork services,
GameCard, identity/persistence, runtime configuration or RVDB. Snapshot copying and final
state publication costs identified in #3 remain separate from these rendering numbers.

## Results

Three fresh-process repetitions per workload; medians in seconds below. Full per-run
values, including spread/outliers, environment and RSS are retained in
[measurement evidence](usqe_milestone4_rendering_measurements.json).

| Families | Baseline construction | New construction | New search | New switch | New scroll | Peak RSS KiB (median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0.0811 | 0.0515 | 0.0168 | 0.0029 | 0.0143 | 78396 |
| 2,000 | 0.8589 | 0.0528 | 0.0168 | 0.0037 | 0.0141 | 79892 |
| 10,000 | 5.0975 | 0.0643 | 0.0166 | 0.0032 | 0.0138 | 84636 |
| 50,000 | bounded timeout | 0.1246 | 0.0195 | 0.0034 | 0.0138 | 109640 |

All predeclared construction/search targets passed. The 50,000-family median maximum
observed event-loop gap was .116 seconds. These synthetic results do not qualify arbitrary
storage devices, cover formats, real ROM discovery or whole-application startup latency.
The fixture's search matches at most 1,000 results; it is not a worst-case all-match query.
The Gallery allocated 30 cards in the reported viewport, bounded by viewport and buffer.

Separate 10,000-family artwork runs alternate a valid 800×1000 image, invalid image,
missing path and no cover. Median construction .0788 seconds, search .0174 seconds,
peak RSS 96,536 KiB. Shared artwork exercises decoding/fallback behavior but does not
represent 10,000 distinct covers or cold storage. Existing artwork/edition regressions
cover correctness separately. No cold OS-cache or universal capacity claim.

## Verification and protected scope

Long-scroll tests cover 100/2,000/10,000/50,000 families and clicking the actual last game.
Repeated replacement/scroll cycles assert bounded cards and no retired top-level cards
after deferred deletion. Tests also cover model replacement, latest-query results,
selected identity after sorting and stable row positions with mixed edition labels.
Existing assertions for list display content now read Qt model data instead of removed
QListWidgetItem objects; their expected content is unchanged.

Themed offscreen review at 1400×800 inspected the top and bottom of the Gallery. Existing
card-size/aspect-ratio and preference checks cover the approved choices. No emulator
launch or live gameplay run was needed. User-observed visual acceptance is not implied.

Protected: actual user data, schemas/IDs, source inventory and publication contracts,
readiness/core policy, artwork assets, shaders, logos, gameplay geometry, emulator
execution and historical milestone records. RVDB stays unchanged. The user approved the implementation report and authorized closure commit/push.
#5–#12 remain unstarted.


All three protected-baseline 50,000-family runs exceeded the 30-second limit (exit 124);
no completed baseline timing is claimed. Baseline code for those runs was loaded from
Git HEAD, preventing the working implementation from contaminating the comparison.

Additional all-match search at 50,000 families: median search .0261 seconds, Compact
transition .0327 seconds. Across three runs, peak RSS sampled after cycles 5/10/15/20
remained flat within each run (111,208 / 111,532 / 111,464 KiB respectively). This is
bounded repeat evidence, not an unlimited-session leak guarantee. Empty/single-game
regressions prevent unnecessary blank-column horizontal scrolling.

Static validation compiled 337 Python files in memory without writing bytecode.
Documentation links, historical-record preservation and bundle parity passed.
RVDB bundle SHA-256 remains
`0c32be3117d31830c5c2e4a8554b2c2f627ed7474c81dbc1697511e5afbf3b9a`.

## Exact changed files

Production (five):
- `ui/library/gallery.py`
- `ui/library/widgets/game_grid.py`
- `ui/library/views/compact_view.py`
- `ui/library/views/details_view.py`
- New `ui/library/views/game_list.py`

Verification (three):
- `tests/test_library_gallery.py`
- New `tests/test_library_rendering_scale.py`
- New `scripts/measure_library_rendering.py`

Documentation/evidence (five):
- `README.md`
- `docs/current_milestone.md`
- `docs/usability_scale_qualified_expansion_roadmap.md`
- New `docs/usqe_milestone4_library_scale.md`
- New `docs/usqe_milestone4_rendering_measurements.json`

No files changed in RVDB. The closure checkpoint includes the approved implementation,
verification evidence and documentation. No production/test changes followed the final
verification; only closure status was updated.

Final complete RetroVault suite: **2,308 passed in 29.77 seconds**.
Final focused rendering/preferences/discovery/Gallery suite: **102 passed**.
No full RVDB rerun was needed because RVDB and its consumer contracts were unchanged.
