# USQE #5 — Compatibility knowledge and useful explanations

Status: **complete following user approval of the implementation report and closure.**
USQE #6–#12 remain unstarted. The original roadmap and earlier acceptance remain protected.

## Scope

Starting RetroVault HEAD: `4b760ae3166a8e79bef689e90ed631ad469db3f7`.
Starting RVDB HEAD: `871b7f8b467db2ff22e6dbd994cef6af0d6a8d44`.

Added `core.fceumm` and `compatibility.core.fceumm.platform.nintendo.nes`, retaining Mesen
and all existing canonical IDs. Existing NES/RetroArch relationships now include FCEUmm.
No schema, validator, builder, core policy, readiness or runtime changes.

Research checked 2026-10-10:
- [Official Libretro documentation](https://docs.libretro.com/library/fceumm/)
- [Upstream README](https://github.com/libretro/libretro-fceumm/blob/master/README.md)
- [Official core metadata](https://raw.githubusercontent.com/libretro/libretro-core-info/master/fceumm_libretro.info)

The playable claim concerns platform-level NES cartridge operation described upstream,
not every game/mapper, a pinned binary version, peripheral qualification or Famicom Disk
System qualification. Software version remains unspecified. The three records are
supporting sources, not three independent runtime tests. Existing evidence dates for
other cores remain unchanged; displaying them does not claim they were rechecked.

## Consumer and UI

Frozen `RVDBEvidenceView` and `RVDBCompatibilityView` preserve each claim's scope,
platform, verdict, evidence, checked date and optional version. The existing core view
has a default-empty compatibility tuple, retaining older constructor compatibility.
`RVDBService.compatibility_records(core_id=..., platform_id=...)` supports either filter
or their intersection, with deterministic ordering. It performs no local runtime lookup.
Different claims are preserved rather than collapsed into a readiness verdict.

The existing RetroArch browser now displays per-platform details and clickable HTTP(S)
evidence links. All source text and link attributes are escaped. Other URL schemes are
rendered as text. Missing evidence, dates and versions are identified explicitly.
The browser calls cores Known rather than Available, and labels the list as RVDB records.
Known, available, configured, qualified and supported have distinct explanations; none
of the latter states is inferred from knowledge. Existing summary fields remain summaries.

## Verification and limits

Validated 59 entities with no schema/relationship errors, and unique IDs. Actual validate
and build subprocess exits were zero. Reversed-source generation matched canonical output;
canonical and installed bytes agree. SHA-256:
`4d99f2b1bff694f26ca1b1ff68b7d4d1816236abb1e64d10a62e14bf20e3eb43`.

RetroVault's installed bundle is intentionally Git-ignored; it was updated through the
existing validated install tool. RVDB's canonical bundle is tracked. Fresh checkouts must
install that bundle through the documented workflow; no force-add or ownership change.

New tests cover production FCEUmm topology/evidence, filtered queries, distinct verdicts,
missing evidence/version, no core-selection lookup, safe markup/URLs and empty UI state.
Existing inventory assertions are updated from 57 to 59 entities and six to seven cores;
Mesen and Sega relationship assertions retain their existing edges. No platform was promoted.

Themed offscreen UI review inspected FCEUmm details at 1400×900. No emulator launch,
installation, controller/save qualification or user-observed gameplay acceptance occurred.
Master System remains a candidate; SG-1000 remains conditional. No expansion is included.

Protected: user data and local-file identities, schemas/existing IDs, readiness/core policy,
production assets, shaders/logos/geometry, runtime configuration, emulator lifecycle and
historical milestone records. Documentation updates affect current status only.

## Approval checkpoint

The user approved closure commits/pushes. No #6 work is authorized; project implementation
is paused for a separate read-only ChatGPT export review.

### retrovault changed files

- `README.md`
- `docs/current_milestone.md`
- `docs/usability_scale_qualified_expansion_roadmap.md`
- `docs/usqe_milestone5_compatibility.md`
- `services/rvdb/models.py`
- `services/rvdb/service.py`
- `tests/test_retroarch_page.py`
- `tests/test_rvdb_service.py`
- `ui/pages/retroarch_page.py`

### rvdb changed files

- `README.md`
- `data/compatibilities/core.fceumm.platform.nintendo.nes.yaml`
- `data/cores/libretro/fceumm.yaml`
- `data/frontends/retroarch.yaml`
- `data/platforms/nintendo/nes.yaml`
- `docs/current_milestone.md`
- `rvdb.bundle.json`
- `tests/test_build_bundle_v2.py`
- `tests/test_bundle_reconciliation_v2.py`
- `tests/test_fceumm_production.py`
- `tests/test_game_gear_genesis_plus_gx_production_v2.py`
- `tests/test_manifest_v2.py`
- `tests/test_master_system_genesis_plus_gx_production_v2.py`
- `tests/test_mesen_compatibility_production_v2.py`
- `tests/test_mesen_production_v2.py`
- `tests/test_project_paths_v2.py`
- `tests/test_sg1000_genesis_plus_gx_production_v2.py`

## Final verification result

- RetroVault complete suite: **2,311 passed in 36.49 seconds**.
- RVDB complete suite: **407 passed in 8.63 seconds**.
- Focused consumer/UI checks: **29 passed**.
- In-memory compile validation: 337 RetroVault and 84 RVDB Python files.
- Git whitespace checks passed; both historical current-status tails unchanged.
- No unexpected production defect found. Existing exact inventory/count assertions
  required updates for the two new records; their behavioral assertions were preserved.
- Verification preceded the approved closure commit/push. No production/test changes
  followed verification; only closure documentation changed. No #6 work started.
