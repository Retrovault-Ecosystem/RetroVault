# USQE Milestone #3 — Responsive Library refresh and import

Status: **complete following user approval of the implementation report and closure.**
USQE #4–#12 remain unstarted. The original roadmap remains closed.

## Scope and protected checkpoints

RetroVault branch `feature/rvdb-foundation`, starting HEAD
`8b38297aa44332e340480c8b27e04c0e1388f5c6`.
RVDB branch `develop`, unchanged HEAD
`871b7f8b467db2ff22e6dbd994cef6af0d6a8d44`.

The approved work moves initial Library discovery, Refresh and Bulk Import preparation
off the UI thread. It reuses the scanner, identity registry, canonicalizer, artwork
resolver, source persistence and existing per-file atomic migration contracts.
No database, canonical-ID, ROM identity, core-selection or readiness policy redesign.
No user data, gameplay geometry, production presentation assets or emulator execution
changes. The archive runtime change is limited to cancellable discovery listing;
launch extraction retains its existing path.

## Implementation and ownership

- `services/library/discovery.py`: detached requests/results, cooperative cancellation,
  bounded progress and worker preparation using existing services.
- `ui/library/discovery_jobs.py`: one owned worker, one latest pending request,
  generation rejection and application-thread publication. Closing waits for ownership
  to end. A cancelled or obsolete worker cannot publish or flush its archive cache.
- `LibraryController` and `LibraryService`: optional delayed initial loading and one
  publication boundary. Source/artwork configuration and registry snapshots are checked
  before writes. Latest favorite state is projected at publication. All fallible object
  copies are staged before existing live objects are updated, retaining selection references.
- Scanner, identity hashing and artwork lookup check cancellation. Archive listing polls
  cancellation, times out after 30 seconds and terminates only its own listing subprocess.
- MainWindow and Gallery bind startup, source/artwork changes, Refresh and Import to jobs.
  The last committed Library remains browsable. Progress shows observed counts with no
  invented percentage. Cancel is disabled during final publication; Import is disabled
  while busy. Repeated Refresh supersedes older preparation.
- Search, canonical-platform filter, sort/view/card-size preferences, recent/favorites,
  selected identity and scroll positions are restored where still applicable. Initial
  default Name ordering retains USQE #2 startup semantics.

RVDB remains knowledge authority. Local files remain inventory authority; existing stores
own user state. Discovery publishes local inventory only, without changing presentation
resolution, runtime configuration, emulator execution or lifecycle authority.

## Failure and cancellation contract

Before publication, cancellation and worker failure retain the old live Library and
perform no discovery writes. Cancellation is cooperative, not an immediate interruption
of blocking filesystem calls or the entire canonicalization operation.

Publication is deliberately non-cancellable. Persistence is atomic per file, not across
files: an import source or identity migration write may succeed before a later step fails.
Feedback explains this and permits retry. The old live snapshot stays intact if staging
copies fail. A dependent-view refresh failure after publication is reported as saved
Library data with a view-refresh problem, not as a rolled-back save. Archive cache flush
failure is a warning after successful publication.

## Measurements and limits

Baseline measurements preceded implementation. Three repetitions per size used synthetic
unique 128-byte loose NES files, fresh application registry/cache and warm OS cache.
No archive, cover-image or edition-family cost is represented by these timings.
Qt was offscreen with a 5 ms event-loop timer. Values below are medians in seconds.
The baseline measured synchronous phases; the worker measurement measured real job
preparation/publication with a standalone grid only at 100 and 2,000 games.

| Games | Baseline largest event gap | Worker discovery event gap | Worker preparation | UI publication | Worker total |
| --- | ---: | ---: | ---: | ---: | ---: |
| 100 | .007773 | .006007 | .008021 | .002374 | .035615 |
| 2,000 | .057591 | .031440 | .098368 | .014239 | .244195 |
| 10,000 | .252276 | .024733 | .465410 | .061449 | .542083 |
| 50,000 | 1.355267 | .029420 | 2.406481 | .336024 | 2.779174 |

These are development observations, not numerical acceptance budgets or a claim of faster
total work. The measured 50,000-game UI publication gap remained approximately .343 seconds.
Full Gallery rendering at 10,000/50,000 games was not qualified. Repeated-refresh snapshot
copying and rendering can still block the UI. They remain measurement inputs to #4,
not a promise of bounded whole-application latency. Final staging of survivor copies is
covered by regression tests but these historical timings were not rerun after that fix.
Temporary raw measurement artifacts did not survive session interruption; this table
preserves the recorded results and method, not a claim that those raw files are retained.

## Verification

- Focused discovery/service/Qt integration suite: **28 passed**.
- Complete RetroVault suite: **2,298 passed in 43.99 seconds**.
- Controlled tests cover cancellation during scanning/hashing/archive listing, unchanged
  live state, stale configuration/registry rejection, latest-request-only publication,
  duplicate imports, partial persistence and retry, progress throttling, cache ownership,
  current favorites and browsing preferences, selection/scroll preservation, worker failure,
  shutdown and 20 repeated worker lifecycles without retained QThreads.
- An unrelated child process remains alive during cancelled archive listing.
- A new failure-injection test exposed partial live-object mutation during staging; this
  was corrected by staging all copies before updating survivors.
- Existing five platform-pipeline cases now wait for asynchronous initial loading; their
  original presentation/runtime assertions remain intact. Empty-source startup does not
  create an unnecessary worker or block normal shutdown.
- Offscreen visual review at 1,100 and 1,600 pixels showed readable progress/cancellation
  controls in the existing toolbar and preserved Library appearance. No gameplay run.
- Tests use isolated temporary configuration/data/cache and synthetic fixtures.
- AST validation of all 334 tracked/new Python files and imports of the discovery,
  publication and MainWindow boundaries passed. Git whitespace and local documentation
  link checks passed; historical current-milestone content remains byte-for-byte unchanged.
- RVDB canonical/installed bundle parity remains intact; SHA-256:
  `0c32be3117d31830c5c2e4a8554b2c2f627ed7474c81dbc1697511e5afbf3b9a`.

## Deferred work and approval boundary

No general task framework, storage-engine replacement, rendering virtualization, numeric
performance SLA, gameplay customization, platform expansion or USQE #4 implementation.
Real slow/network filesystem responsiveness is not comprehensively qualified. Qt offscreen
review is not a claim of user-observed desktop acceptance. RVDB remains untouched.

The user approved the implementation report and authorized continuation through closure.
This checkpoint records the approved implementation and verification; no USQE #4 work
is included. No production or test changes were made after the reported verification.
