# Milestone #9 — One complete platform pipeline: NES

NES is the selected reference platform. The qualification connects the existing
RVDB, Library, persistence, presentation and runtime owners; it does not introduce
a second implementation of any of them.

## Completion contract

A complete run must:

1. Snapshot the validated installed RVDB bundle and stage a byte-identical copy of
   an explicitly selected, user-owned `.nes` ROM in a fresh qualification directory.
2. Establish isolated XDG configuration, cache and data roots before constructing
   application services, and persist the source through ImportSourceStore.
3. Obtain the target from LibraryController/LibraryService's actual scan,
   registration and family projection, with canonical NES platform identity and an
   opaque local-file identity. The runner must not construct a replacement Game.
4. Resolve the installed qualified NES core using CoreResolver and the existing policy.
5. Persist and read back a favorite, collection membership and game presentation
   preference through the existing stores/application services.
6. Resolve the effective production package while preserving the saved preference.
7. Launch the scanned edition through GameLaunchController, using the actual
   LibraryController.record_played callback. Failed/cancelled launches must not add history.
8. Observe a bounded live session, Stop it, shut down the owned runtime and clean
   session resources without changing protected user files.
9. Reconstruct the Library and presentation services in a separate interpreter from
   an unrelated working directory. Source, identity, favorites, collections, saved
   preference, effective presentation and Recently Played must match the persisted
   post-launch snapshot.

Process/configuration evidence and human visual/gameplay observation are recorded
separately. A successful emulator process is not proof of pixel correctness or input.

## Ownership and production correction

The runner uses RVDBLibraryResolver, LibraryController, LibraryService, RomScanner,
IdentityRegistry, LibraryState, CollectionStore, PresentationStore,
LibraryPresentationStudioService, PresentationCompositionFactory,
GameLaunchController, CoreResolver, ProcessLifecycleAdapter and RetroArchLauncher.
Their existing validation and runtime owners remain authoritative.

The integrated UI test demonstrated that PlaylistsPage's GameDetails received the
shared launch controller but neither the shared PresentationStore nor the launch
presentation resolver provider. MainWindow now passes both through PlaylistsPage.
Library and Playlists consequently expose the same saved presentation state and use
the same presentation resolution path. No runtime policy, asset or schema change was
needed. The regression test launches from both surfaces, stops, polls back to IDLE,
and verifies persisted identity/history and collection/favorite state.

## Repeatable live command

From the repository, with its configured installed emulator/core/assets:

```bash
.venv/bin/python -B -m scripts.qualify_retroarch_runtime \
  --pipeline --platform nes \
  --rom '/absolute/path/to/user-owned/game.nes' \
  --output '/absolute/path/to/a-new-qualification-directory' \
  --seconds 30
```

From an unrelated working directory, set `PYTHONPATH=/home/oilcan/retrovault` and use
`/home/oilcan/retrovault/.venv/bin/python`. The output directory must not already exist.
The pre-existing bounded runtime and `--via-controller` modes remain supported.
At Milestone #9, `--pipeline` rejected platforms other than NES.
[Milestone #10](milestone10_platform_expansion.md) extends it to SNES and Genesis. It returns a failing exit
status when any required stage fails, even if the emulator successfully ran.

The staged ROM and isolated durable profile remain in the report directory to permit
inspection and repeat restart checks. They are qualification artifacts, not session
transients. ROM bytes are never added to source control or published. Archive scan
cache and disposable session files remain distinct. The real user profile, original
ROM, primary RetroArch config and installed bundle are hash-checked for preservation.

## Knowledge limits

The current NES RVDB record lists `core.mesen` compatibility. RetroVault's separately
qualified NES execution policy selects FCEUmm. The report records both without
changing or conflating those authorities. The installed and producer bundles remain
identical; no RVDB source/build changes are required for this milestone.

The live fixture is Duck Tales 2. It has no canonical game record in the current RVDB
source; the correct result is a populated `rvdb_platform_id` and an empty
`rvdb_game_id`. Its local identity, favorites, collections, presentation and history
remain fully functional. This qualification does not claim a complete NES title
catalog or introduce heuristic metadata matching.

## Verification

- Full suite: **2,035 passed** (`build/milestone9/automated-tests.log`).
- Focused pipeline/runtime/Playlists checks: **44 passed** before the final four
  runner guard tests were included in the full suite.
- New integration coverage uses real filesystem discovery, identity/persistence,
  presentation selection and fresh-process restart, replacing emulator execution only.
- Negative scenarios cover malformed bundle, missing ROM/core/package, spawn failure,
  cancellation, history write failure, disappearing restart source, profile preservation,
  refresh without duplicate identity, environment restoration, existing output rejection,
  non-NES scope rejection and a failing CLI exit status after an incomplete pipeline.
- UI integration constructs MainWindow and verifies both Library and Playlists against
  the same isolated persisted NES entry. Dialog choices and emulator execution are
  substituted for deterministic automation.

The final runner preservation guard also rejects newly created JSON files in the real
user profile. After that addition, **28 pipeline/runtime checks passed**
(`build/milestone9/final-pipeline-tests.log`); compilation and diff checks passed.

The live run from `/tmp` is retained at `build/milestone9/nes-live/report.json`:

- Duck Tales 2 ran for **30.028 seconds** using the scanned entry and FCEUmm.
- All twelve recorded stages passed, including actual history persistence and
  reconstruction in a fresh interpreter.
- The favorite, qualification collection, saved overlay reference, effective package,
  source definition and local-file identity matched after restart.
- Stop/shutdown succeeded; no owned emulator/probe process, cleanup error or disposable
  session file remained. No warnings were reported.
- Eleven protected files (original ROM, primary config, bundle and user JSON files)
  were unchanged. The final audit also verified no new JSON files in the normal profile.
- Selected artwork SHA-256 and effective viewport/overlay settings match Milestone #8.
  `build/milestone9/acceptance-evidence.json` records that comparison.

The producer and installed consumer bundle share SHA-256
`0c32be3117d31830c5c2e4a8554b2c2f627ed7474c81dbc1697511e5afbf3b9a`.

**Milestone #9 is complete and formally closed.** The user requested a second
30-second live run and explicitly confirmed: "Yes, Visuals and gameplay were correct!"
The repeat run at `build/milestone9/nes-visual-confirmation/report.json` passed all
pipeline stages, clean shutdown, state restoration and file preservation.
`build/milestone9/acceptance-evidence.json` records the human confirmation separately;
raw machine reports retain their original process-only observation fields.

## Explicit exclusions

Complete NES catalog coverage, additional platforms/cores, archive expansion, artwork
or shader redesign, emulator save-state management, input-remapping features,
performance work, packaging, cloud synchronization, and qualification of every NES
title/display configuration are outside scope. No persistent user-data format,
production viewport or executable-activation behavior is changed.
