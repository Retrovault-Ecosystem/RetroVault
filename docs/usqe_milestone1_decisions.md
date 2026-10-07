# USQE Milestone #1 — Product Decisions and Qualification Baseline

Status: **complete as an approved decision and documentation milestone**. No production implementation or new qualification campaign is part of this closure. **USQE #2–#12 remain unstarted.**

This record implements the user's approved decision packet and documentation-only closure authorization. See the [approved USQE roadmap](usability_scale_qualified_expansion_roadmap.md) for sequence, phase boundaries and dependencies. The original [14-milestone closure](milestone14_final_integration.md) remains permanently closed and unchanged.

## Protected starting checkpoints

- RetroVault, `feature/rvdb-foundation`: `0bb2f0904dfee707bbd486683719dfda019efc07`.
- RVDB, `develop`: `e03d6de9d5b2677343758e11d2fcdb5838a284f3`.

Both were confirmed clean at those heads before this documentation work. Prior roadmap test and bundle evidence remains prior evidence, not a newly run suite. User data, production/test code, schemas, runtime configuration, identity contracts, readiness/core policy, assets and gameplay geometry are unchanged.

## A. Customization

### APPROVED DECISIONS

USQE #2's first slice has exactly three controls:

1. Preferred opening Library view: existing Gallery, Details or Compact.
2. Bounded Gallery card-size choices including the approved existing size.
3. Preferred normal browsing sort, using existing Name/Year behavior while preserving special ordering such as Recently Played.

Library display preferences belong in application configuration, **not PresentationStore**. Reuse ConfigLoader/ConfigWriter, SettingsService and existing Library views. PresentationStore retains game-presentation ownership.

Preserve approved defaults and unchanged behavior until users explicitly choose a preference. Preview in memory where feasible; Apply validates and persists; Cancel restores the last applied preferences; Reset-to-approved-defaults changes the preview and requires Apply to persist. A failed save preserves previous durable settings and reports failure accurately. Later virtualization must preserve these preference meanings.

### PENDING EVIDENCE / FUTURE SELECTIONS

Exact smaller/larger card dimensions, responsive layout details and UI presentation need bounded #2 visual review. No global theming, arbitrary shader controls, bezel selection, gameplay geometry controls or broad PresentationStore changes are included. Metadata visibility and further customization remain later choices.

## B. Scale and performance

### APPROVED DECISIONS

| Workload | Visible games | Meaning |
| --- | ---: | --- |
| Small | 100 | Everyday correctness/UI regression |
| Reference | Approximately 2,000 | Comparison with previously measured scale |
| Large | 10,000 | Whole-library processing/rendering costs |
| Stress/reference | 50,000 | Scaling behavior and limits |

These are **test workloads, not capacity promises**. Each fixture records visible families, physical files/editions, archive count, artwork count, bytes, source overlap and edition distribution. Separate in-memory rendering from filesystem scans, identity work, archive inspection and artwork loading. Include cold/warm application-cache conditions, missing/bad artwork, duplicate/overlapping sources and interrupted operations. Do not claim a cold OS cache merely from an empty application cache.

Measure the protected baseline before optimizing using a recorded machine, interpreter, Qt version and display configuration. Separate discovery, identity processing, state commit, view construction and artwork costs. Repeat runs and report median, spread and outliers. Capture event-loop delay, response latency, first usable view, filtering/view transitions, memory and widget/image counts. Establish numerical budgets from those measurements before implementation.

The [historical startup study](startup_performance.md) measured 1,968 visible games at about 3.205 seconds with the user interpreter and 2.929 seconds with the repository environment under its stated warm-filesystem/offscreen conditions. It is not a new benchmark or a threshold for larger libraries.

Correctness contracts for #3/#4:

- Cancellation before commit leaves durable state unchanged.
- One authoritative state-publication owner; no partial visible commit.
- Older results cannot overwrite a newer accepted result.
- Browse the last committed library while discovery runs.
- Selection follows stable identity, not a changing row number.
- Latest query wins; stale search results do not reappear.
- Progress reports actual phases/work; unknown totals do not receive invented percentages.
- Define and expose any short non-cancellable commit phase honestly.
- After virtualization, widgets/images are bounded by visible region plus an explicit buffer.
- Unexplained memory accumulation across repeated operations is unacceptable.

### PENDING EVIDENCE / FUTURE SELECTIONS

Exact fixture distributions, repeat counts, timing/memory thresholds, cancellation bounds and render-buffer sizes are unmeasured. Select them from the baseline procedure, not arbitrary promises. No performance optimization or synthetic fixture generation has occurred in #1.

## C. Controllers

### APPROVED DECISIONS

Initial set: keyboard/one player; one standard wired gamepad; wireless equivalent only if available and useful; two standard gamepads; two identical gamepads if available. Maximum initial player scope is two. Test RetroArch and native Snes9x separately rather than assuming profile equivalence.

Explicit Player 1/Player 2 assignment; no silent reassignment; reconnect an identifiable device to its previous slot; ambiguity requires explicit reassignment instead of guessing. Disconnect retains assignment with non-destructive feedback. No automatic pause without explicit approval and reliable backend support.

Preserve existing RetroArch mappings, native profiles and keyboard shortcuts. Reuse existing backend/session/configuration boundaries. Light guns, steering wheels and other specialized peripherals remain outside the initial scope.

### PENDING EVIDENCE / FUTURE SELECTIONS

Exact device models, transports, available identical pairs, backend mapping details and suitable multiplayer fixtures are not selected or qualified. No device purchase or universal controller support is implied.

## D. Saves

### APPROVED DECISIONS

Qualify same-backend continuity first. Keep separate: SRAM/battery-style saves, emulator save states, configuration/profile files, physical-file identity and backend-specific formats. Preserve existing saves and isolate physical editions. No automatic cross-backend sharing, assumed cross-core save-state compatibility or format conversion without evidence.

#7 must establish RetroArch's actual effective save destinations and collision behavior before changing policy. Native Snes9x's identity-derived isolation is not proof of equivalent RetroArch behavior.

Representative case categories:

- One observable SNES in-game save through the RetroArch Snes9x core.
- The same fixture through native Snes9x, using separate backend storage.
- Another physical edition with a colliding basename.
- One same-version save-state round trip on each selected backend route.
- One additional save-capable NES or Genesis fixture from available user-owned content.

Real acceptance must prove: launch -> create identifiable progress -> save -> exit normally -> fresh emulator process -> reload -> recover that progress. Verify another physical edition remains unaffected. A file's existence alone is insufficient. Determine save flush behavior; Stop is not automatically equivalent to saving. Use disposable copies for failure/recovery tests and protect existing saves before any future path change.

### PENDING EVIDENCE / FUTURE SELECTIONS

Exact titles/hashes, versions, destinations, format compatibility and actual round-trip results remain pending. Cases are planned categories, not completed tests. Backup/import/recovery interface details belong to #7's bounded design, not a cloud-sync or universal-conversion feature.

## E. First expansion batch

### APPROVED DECISIONS

**Master System is the first target candidate. SG-1000 is conditional only. Maximum batch size: two platforms.**

SG-1000 joins only if #5–#8 establish acceptably low incremental qualification cost without significant distinct presentation, controller, save, firmware or runtime requirements. Game Gear remains reserve-only because handheld presentation requires separate qualification. Begin with loose cartridge-file cases to distinguish platform behavior from archive behavior; archive coverage can be a separate representative row.

The read-only decision audit found existing canonical records, `.sms`/`.sg` knowledge, compatibility records and a locally resolvable shared Genesis Plus GX core. Those observations establish neither successful runtime qualification nor production support. Optional boot behavior is excluded from the initial candidate scope; fixture-specific firmware assumptions still need checking.

### PENDING EVIDENCE / FUTURE SELECTIONS

Actual Master System/SG-1000 qualification, supported presentation binding, game fixtures, controller/save behavior and readiness remain pending. No core installation, artwork, package, readiness change or platform support is authorized by candidate selection. SG-1000 inclusion is not automatic.

## F. Presentation qualification

### APPROVED DECISIONS

Qualify the **family envelope** separately from the **platform/backend binding**. Preserve technically correct content fully visible, proportioned and oriented. Never crop, stretch, distort or arbitrarily resize gameplay simply to fill artwork. A 4:3 envelope does not force every framebuffer to 4:3; a 16:9 screen does not justify stretching 4:3 content.

| Family | Required evidence |
| --- | --- |
| CLASSIC_4_3 | Recorded envelope/canvas, justified content display aspect, containment calculations, all intended edges, orientation, resolution/scaling, runtime evidence and targeted human acceptance. |
| WIDESCREEN_16_9 | The same plus evidence the selected content/mode genuinely uses the intended wide aspect. |
| Mixed/exception | Explicit modes and supported transitions; distinguish startup selection from unqualified mid-game switching. |
| Handheld | Native/intended proportions and a justified separate envelope. |
| Vertical | Rotation/orientation verified before containment, including artwork/control orientation. |
| Dual-screen/unusual | Explicit screen arrangement, gap and input requirements; not assumed to be one wide image. |

Collect package/config hashes, runtime version, fixture/content mode, output dimensions, automated geometry evidence and targeted human acceptance where applicable. Process all applicable 4:3 members of an approved bounded batch before its 16:9 and mixed members. Empty categories do not require inventing a platform. Existing approved NES/SNES/Genesis packages remain protected.

### PENDING EVIDENCE / FUTURE SELECTIONS

New envelopes, package bindings, display configurations and human visual results remain pending #8/#9. Recognized capability names are not automatically qualified physical layouts. No live geometry application is authorized.

## G. Readiness/support language

### APPROVED DECISIONS

These are distinct product/evidence facts, not a replacement code state machine:

| Term | Definition |
| --- | --- |
| KNOWN | Canonical RVDB identity exists; no installation/support inference. |
| AVAILABLE | Applicable local executable/core resolves and passes its file checks; no launch guarantee. |
| CONFIGURED | Required local selections/paths/policies are structurally valid for the stated route. |
| QUALIFIED | A stated platform/backend/version/configuration/fixture scope passed recorded acceptance. |
| SUPPORTED | RetroVault deliberately offers and maintains that workflow within documented qualification limits. |
| EXPERIMENTAL | Explicit opt-in workflow with incomplete qualification and stated limits. |
| UNSUPPORTED | RetroVault does not offer/guarantee the specified workflow; not a statement that the external emulator cannot do it. |

Preserve CoreResolution statuses, presentation READY/UNCONFIGURED, master-presentation QUALIFIED/CAPABILITY_ONLY and RVDB playability values. Presentation READY is not universal platform readiness. Knowledge != availability != configuration != qualification != product support.

### PENDING EVIDENCE / FUTURE SELECTIONS

UI labels and presentation of these facts are future work. No authoritative enum changes or automatic readiness promotions are approved.

## H. Representative qualification matrix

### APPROVED DECISIONS

Extend [existing RetroArch](../scripts/qualify_retroarch_runtime.py) and [native](../scripts/qualify_standalone_runtime.py) runners/reports when their later milestones authorize implementation; do not create a general test framework without demonstrated need.

Each case records:

- Case ID, canonical platform, physical fixture identity/content hash and loose/archive/member form.
- Backend, core/emulator version and binary hash.
- OS, relevant drivers, display resolution/scaling.
- Presentation family, package/config hashes and content mode.
- Device class/model/transport, mapping and player assignment.
- Save mechanism/format, isolated location and expected recovery.
- Launch/Stop/restart/failure/cleanup/history results.
- Automated evidence location and targeted human visual/input/save acceptance where required.
- Date, tested repository checkpoints, explicit result and limitations.

Outcomes: **pass, fail, blocked, not run, not applicable**. Missing evidence never becomes pass.

Representative rows: existing NES/RetroArch lifecycle/presentation/input; SNES/RetroArch real save round trip; SNES/native lifecycle/profile/save round trip; Genesis/RetroArch geometry/input; one two-player case; one edition-collision case; controlled failed-startup/cleanup-retry case. Add Master System and conditional SG-1000 rows only in #9. Reuse shared contract tests instead of every device × game × display × backend combination.

### PENDING EVIDENCE / FUTURE SELECTIONS

Concrete case fixtures, report extensions, new runner code, dates and actual future results remain pending. Existing historical qualification is not automatically extended to new combinations.

## I. Research-gated register

None of these is authorized for implementation merely by being listed:

| Gate | Required evidence before proposing implementation |
| --- | --- |
| Continuous mid-game geometry | Demonstrated content need and safe backend application mechanism. |
| Unwired dynamic presentation application | Proof generated changes can be applied during execution. |
| Broad schema redesign | Concrete consuming need not represented by existing contracts. |
| Scalar relationships | End-to-end producer/graph/bundle/consumer contract. |
| BIOS/firmware modeling | Selected systems, requirement semantics and local verification rules. |
| Unresolved canonical platform boundaries | Evidence supporting identity/relationship decisions. |
| Expanded historical indicators | Historical evidence and real observable runtime events. |
| Additional standalone backends | Selected target, user value and lifecycle/capability requirements. |
| Multi-process persistence writers | Actual supported concurrent-writer requirement. |
| Cross-file transactions | Concrete operation insufficiently served by atomic/retryable writes. |
| Windows/macOS portability | Explicit target and dependency/qualification assessment. |
| Exhaustive all-game certification | Replace universal promise with bounded representative evidence and limits. |

Cache reclamation, archive quotas and ambiguous legacy-entry cleanup remain separately approved maintenance/policy work. No deletion is authorized. Research can conclude a limitation should remain.

## J. Four accepted prerequisites; sequence unchanged

1. #2: a small validated application-preference contract.
2. #3: discovery separated from state publication, with one commit owner.
3. #7: actual RetroArch save destinations/collision behavior established before policy changes.
4. #8: presentation capability names kept distinct from qualified physical layouts.

No prerequisite requires reordering the approved 12 milestones. Device models, exact game/save fixtures, numerical performance budgets, SG-1000 inclusion and future live results are deliberately unresolved; resolve them in the relevant bounded milestone with better evidence.

## Documentation-only closure

The user approved this decision baseline and explicitly authorized documentation-only closure. Only the two new RetroVault documents and each repository's README/current-status entry are changed. Original historical records remain unchanged. No code/tests/schemas/runtime/user-data/assets/readiness changes, benchmarks, regression runs or emulator launches form part of this closure.

Verification: compare the documentation to approval; validate numbering/dependencies, links and starting hashes; audit the six-file-only diff and whitespace; explicitly stage; create one documentation commit per repository; push normally; confirm clean worktrees, local/remote equality, zero divergence and protected starting ancestry. Final hashes are recorded in the closure report, not embedded in their own commits.

USQE #1 is a closed planning baseline, not a claim that its future acceptance tests have run. USQE #2–#12 remain unstarted and require their own authorization. The original 14-milestone roadmap remains closed.
