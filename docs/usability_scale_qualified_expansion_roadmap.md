# RetroVault + RVDB — Usability, Scale and Qualified Expansion (USQE)

Status: approved new 12-milestone roadmap. **USQE #1 is complete as a decision/documentation milestone. USQE #2–#4 are complete; #5–#12 are unstarted.**
This is a separate roadmap, not Milestone #15. The original 14-milestone roadmap remains permanently closed and protected. No feature implementation is authorized by this document alone.

See the [Milestone #4 implementation report](usqe_milestone4_library_scale.md) for rendering measurements and review status.
## Protected starting checkpoints

| Repository | Branch | Protected starting HEAD |
| --- | --- | --- |
| RetroVault | `feature/rvdb-foundation` | `0bb2f0904dfee707bbd486683719dfda019efc07` |
| RVDB | `develop` | `e03d6de9d5b2677343758e11d2fcdb5838a284f3` |

The [original M14 closure record](milestone14_final_integration.md) remains historical and unchanged. Its prior verified evidence includes 2,213 RetroVault tests, 406 RVDB tests, 2,213 clean source-copy RetroVault tests, 57 valid RVDB entities and deterministic canonical/installed bundle parity. These are prior results, not tests repeated for this documentation closure.

Prior bundle SHA-256: `0c32be3117d31830c5c2e4a8554b2c2f627ed7474c81dbc1697511e5afbf3b9a`.

## Approved principles

Preserve the architecture: RVDB owns canonical knowledge; RetroVault owns local inventory, durable user preferences, installed-runtime qualification, presentation policy and execution/lifecycle state. Knowledge is not runtime readiness or product support.

Approved appearance remains the default. Preferences must be reversible, and the user can refine choices as the product develops. Standardized presentation envelopes contain technically correct gameplay; never crop, stretch, distort or arbitrarily resize gameplay merely to fill artwork. Artwork adapts to content. Existing NES/SNES/Genesis packages, geometry, identity contracts and historical acceptance remain protected.

Use existing services, data, profiles and qualification runners. No speculative framework, database redesign, automatic platform promotion or cleanup-only milestone is implied. Research gates remain gates. A Bring It to Life checkpoint follows a stable functional foundation and remains limited to that completed area.

## Approved sequence and phases

Numbers below belong only to USQE. #1 is complete; [#2 implementation and review](usqe_milestone2_customization.md) are approved and complete. #3 is [approved and complete](usqe_milestone3_responsive_discovery.md); #4 is approved and complete; #5–#12 remain **unstarted**.

| Phase | # | Milestone | Objective and prerequisite boundary |
| --- | --- | --- | --- |
| I — Decisions and early usability | 1 | Product decisions and qualification baseline | Approved bounded decisions and evidence requirements; documentation-only closure. |
| I | 2 | Reversible customization, first usable slice | Library opening view, bounded Gallery card size and normal sort; depends on #1. |
| I | 3 | Responsive library refresh and import | Background discovery with cancellation/stale-result protection and one state-publication owner; depends on #1, independent of #2. |
| II — Scale and trustworthy knowledge | 4 | Large-library browsing and rendering | Measured rendering/lookup improvements and bounded visible widgets/images; depends on #1 measurements and #3 update contract; preserve #2 preferences. |
| II | 5 | Compatibility knowledge and useful explanations | Bounded researched records, including FCEUmm coverage, and useful queries; depends on #1 scope. Knowledge must not promote local readiness. |
| III — Reliable play and reusable presentation | 6 | Controller profiles for existing supported backends | Bounded keyboard/gamepad qualification and explicit player policy; depends on #1 decisions and #2 preference conventions. |
| III | 7 | Save policies, recovery and real round-trip qualification | Actual save destinations, edition isolation and real save recovery; depends on #1/#2 and #6 where interaction requires it. |
| III | 8 | Presentation-family qualification and reusable templates | Qualify envelopes separately from platform/backend bindings; depends on #1/#2 and #5 where knowledge is needed. |
| IV — Controlled expansion and production confidence | 9 | First complete platform expansion batch | Master System first candidate; SG-1000 conditional; maximum two platforms; depends on #5–#8. |
| IV | 10 | Sustained-session and recovery qualification | Bounded longer-running representative coverage, not every-game certification; depends on #6/#7/#9. |
| V — Reproducible delivery | 11 | Safe RVDB delivery and rollback | Trusted compatible bundle acquisition, atomic activation and recovery; depends on #1 delivery decisions and #5 consumer expectations. |
| V | 12 | Reproducible Linux distribution and acceptance | One selected Linux distribution target; depends on #10/#11 and the completed release feature set. |

Dependency chains: library scale `#1 -> #3 -> #4`; play/expansion `#1 -> #2 -> #6 -> #7`, plus `#1 -> #5 -> #8`, converge on `#9 -> #10 -> #12`; delivery `#1 -> #5 -> #11 -> #12`.

The approved execution sequence remains 1 through 12. Potential independence is not authorization to start milestones concurrently. #2/#3, library work/#5, and presentation research/input-save work have separable areas; integration checks remain necessary. No discovered prerequisite requires reordering.

## Bounded milestone outcomes and exclusions

- **#2:** Preview/apply/cancel/reset with validated application preferences and unchanged defaults. No global theme system, arbitrary shaders, bezel selection or gameplay geometry controls.
- **#3:** Responsive discovery, honest progress, cancellation before commit, old-result rejection and browsing the last committed library. No concurrent persistence writers or storage-engine replacement.
- **#4:** Establish budgets from measurements; bound visible widget/image work and preserve identity-based selection. No speculative indexing or rewriting views that already meet their budgets.
- **#5:** Evidence-backed bounded knowledge and explanations separating known/available/configured/qualified/supported. No schema redesign or automatic core-policy changes.
- **#6:** Selected standard devices and at most two players; preserve existing profiles. No specialty peripheral programme or unapproved automatic pause.
- **#7:** Recover meaningful progress after a fresh process and leave other editions unaffected. No assumed state-format portability, cloud saves or automatic cross-backend sharing.
- **#8:** Approved bounded batch order: applicable 4:3, then 16:9, then mixed. Do not force handheld/vertical/dual-screen systems into these groups. No recalibration of protected packages or unproven live geometry switching.
- **#9:** Each selected platform must pass complete library-to-runtime qualification. No unlimited expansion, new standalone backend or firmware-heavy unresolved platform merely to fill the batch.
- **#10:** Pre-agreed durations/workloads, recovery, cleanup and input/save/presentation continuity with transparent limits. No universal compatibility claim.
- **#11:** Agree delivery policy and trusted provenance before implementation. Preserve the last usable bundle and support rollback/offline behavior. No rebuilding producer knowledge inside the consumer or silently updating user preferences.
- **#12:** Clean installation, prerequisites, upgrade/rollback and removal that preserves user data. No Windows/macOS portability or expanded support claims without separate approval.

Bring It to Life checkpoints are expected after functional acceptance in #2–#9, #11 and #12; #10 reviews feedback rather than redesigning visuals. Live qualification is chiefly needed in #6–#10 and #12. No future visual or live acceptance is recorded as already passed.

## Repository responsibilities

#2–#4 and #6–#7 primarily affect RetroVault. #5 spans researched RVDB records and consumer explanation/validation. #8 is primarily RetroVault, with RVDB changes only for demonstrated knowledge needs. #9 and #11 require coordinated producer/consumer checks. #10 primarily extends RetroVault evidence. #12 packages RetroVault against a pinned RVDB artifact. This does not authorize simultaneous changes in both repositories unnecessarily.

## Decision baseline and future authorization

The authoritative [USQE #1 decision baseline](usqe_milestone1_decisions.md) separates **APPROVED DECISIONS** from **PENDING EVIDENCE / FUTURE SELECTIONS**, including the qualification matrix and research register. It is the planning input for later milestones, not an implementation of them.

USQE #1 closed with published documentation checkpoints: RetroVault `4bcfa25110cb4af39b4be5942e27ba53d71cbe9a` and RVDB `871b7f8b467db2ff22e6dbd994cef6af0d6a8d44`. The protected starting commits remain ancestors. The user authorized #2 implementation separately; then approved its implementation report and authorized final closure commit/push. #3 has not been authorized.
