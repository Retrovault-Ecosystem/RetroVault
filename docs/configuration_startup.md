# Configuration and startup reproducibility

## Milestone #14 integration status

Milestone #14 closes the approved 14-milestone roadmap. No Milestone #15 has begun.
See [M14 evidence and limits](milestone14_final_integration.md). RVDB `validate` (or `v`)
and `build` now return nonzero process status on failure. Build rejects duplicate IDs
and replaces its output atomically only after successful serialization/flush.
The existing consumer bundle installation and configuration ordering below are unchanged.
Standalone settings distinguish a successful save with a failed refresh from a write failure.
Historical runtime files are not automatically deleted; archive extraction is retained cache.

## Setup

Use the repository's virtual environment, not a global Python installation with
accidental dependencies. From the RetroVault checkout:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
# Required only for development/tests and rebuilding approved artwork:
.venv/bin/python -m pip install -r requirements-dev.txt
```

PyYAML is an application dependency. Pillow and pytest are development/tooling
dependencies. RetroArch, libretro cores and an optional 7-Zip executable are external
installations; installing Python dependencies does not install them.

The RVDB runtime bundle remains explicitly delivered, Git-ignored application data.
Obtain a bundle from the RVDB producer's validated build, then install that exact file:

```sh
.venv/bin/python -m scripts.install_rvdb_bundle /absolute/path/to/rvdb.bundle.json
.venv/bin/python -B -m scripts.check_startup
.venv/bin/python app.py
```

The installer validates staged bytes with RVDBService before atomic replacement and
prints their SHA-256. Validation/copy/replace failure preserves an existing bundle.
It neither downloads data nor rebuilds RVDB, and runtime startup never searches a
sibling repository. Producer schema/build validation remains RVDB's responsibility;
the consumer installation validates the portable bundle contract.

Launch from another directory with the absolute paths to the environment and app:

```sh
/absolute/path/to/retrovault/.venv/bin/python /absolute/path/to/retrovault/app.py
```

Application resources, including RVDB, are resolved from the checkout, not the
working directory. For module-based diagnostic commands from another directory,
set `PYTHONPATH` to the checkout explicitly.

## Configuration contract

`config/retroarch.yaml` supplies portable defaults. User overrides live at
`$XDG_CONFIG_HOME/retrovault/runtime.json`, falling back to
`~/.config/retrovault/runtime.json`. Recursive dictionary merging and whole-list
replacement are unchanged; unrelated extension keys are retained. Known fields
are validated before consumers use them. Source IDs are unique, enabled flags are
booleans, and local source records include ID, name, type and absolute/tilde path.

Directory/configuration-file values accept absolute paths or `~`, not paths relative
to the working directory. Empty paths mean unconfigured. Executables may be an
absolute/tilde path or a bare PATH command, but not a relative path containing `/`.
No environment-variable substitution is performed inside saved values.

Fresh defaults contain no Library sources and no assumed core directory. Existing
user overrides remain effective and are not rewritten during startup. Settings can
save an empty Library or create the first source when a directory is supplied.
The configured RetroArch executable must pass the existing validation when saving
runtime settings; app startup itself does not require an installed emulator.

ConfigWriter validates known fields and writes through a unique temporary file,
flush/fsync and atomic replacement. It preserves unrelated keys. Filesystem errors
are reported in Settings; malformed configuration is never silently reset. Startup
shows the failing file/field and exits before Library construction on invalid
configuration. Correct the file and restart. This is not a multi-process transaction
or a synchronization service.

## Startup and activation

Preflight reads settings, validates the bundle, reports resolved locations and
checks basic executable/core/config availability. `python -B` also suppresses Python
bytecode writes. Preflight does not scan ROMs, migrate identities, create user stores,
invoke RetroArch or install assets. Its output is configuration evidence, not a
claim that a core or presentation is playable. Exit 1 indicates invalid configuration
or unavailable RVDB; missing local emulator prerequisites are warnings so setup can
continue.

Missing/invalid RVDB permits the application shell and Settings to open, but blocks
Library scanning/import until a valid bundle is installed and the application is
restarted. This prevents silent legacy-only identification such as the earlier
Genesis defect. Normal configured Library startup retains its established identity
registration/migration behavior. Disposable archive caches retain their invalidation
rules and do not become identity or runtime validation authority.

| Change | Takes effect |
| --- | --- |
| RetroArch executable | After application restart; Settings keeps showing the restart notice until then |
| RVDB bundle | After application restart |
| Primary RetroArch config | Next launch |
| Core and production overlay/shader roots | Next launch, with existing validation |
| Source path changed through Settings | Existing live Library reload signal |
| Artwork/overlay browser root | Existing page refresh signals |

The launcher reads one fresh configuration snapshot for package roots and primary
selection for each launch. The shared executable remains the one selected at window
construction. Separate UI operations may reload settings; there is no global frozen
configuration and no promise of atomic external edits spanning multiple user stores.

## RetroArch primary configuration

Optional `retroarch.primary_config` is exposed in Settings. Priority is explicit
`LaunchProfile.config`, then the saved setting, then compatibility discovery:
Flatpak config, XDG config, native `~/.config/retroarch/retroarch.cfg`, and
`~/.retroarch.cfg`. Settings/preflight show the selected source. Automatic discovery
is deterministic but does not infer which installation a wrapper executable uses;
set the explicit path when multiple installations exist.

Canonical production launches isolate the selected primary config even without a
Wayland video-driver override. Missing primary configuration blocks that production
launch with a diagnostic. Space- and tab-separated directives are supported.
Duplicate controlled directives and `#include` configurations fail explicitly;
select a standalone config rather than silently leaving competing presentation
settings active. Persistent RetroArch configuration is never rewritten.

The existing session, overlay, core-options, shader, containment, adaptive bezel and
cheat services still own their layers. One ordered pipe-delimited `--appendconfig`
argument, qualified core geometry, shader behavior and process-group cleanup remain
unchanged. The qualification runner honors the same saved primary-config choice.

## User data and caches

Durable filenames and schemas for favorites/recent history, identities, collections
and presentation assignments remain unchanged. Active transient owners and archive
classification/extraction use `$XDG_CACHE_HOME/retrovault`, with `~/.cache/retrovault`
as fallback. Empty or relative XDG values use the home fallback; preflight reports
relative values. Explicit injected directories still take precedence.

Changing the cache root does not move/delete older caches. Cold caches may rebuild;
archive extraction caches remain separate from one-session transient cleanup.
Existing explicitly saved artwork and asset paths are honored as written.

No new platforms, artwork, shaders, RVDB schemas, identity migration, background
scanning, installer distribution, hot executable switching, automatic downloads,
cross-platform qualification or cloud/multi-process synchronization are included.


## Milestone #7 qualification and closure

Completed 2026-09-30. Evidence is retained under `build/milestone7/`:

- `automated-tests.log`: 1,999 passed; `final-settings-tests.log`: 82 passed after
  the final persistent restart-notice correction.
- `startup-diagnostics.json`: no errors or warnings from an unrelated working directory.
- `nes/report.json`, `snes/report.json`, `genesis/report.json`: successful bounded
  production launches from `/tmp`, clean Stop/shutdown, no remaining process group
  or session transients, and unchanged persistent RetroArch configuration.
- `acceptance-evidence.json`: selected PNG hashes and effective presentation settings
  match the previously user-accepted NES/SNES/Genesis baseline. These reports are not
  screenshots or a substitute for human visual observation.
- `preserved-files-before.json`: baseline for the 12 checked user/configuration/artwork
  files; all remained unchanged after qualification.

Dependency consistency and compilation checks passed. The RVDB producer and consumer
bundle SHA-256 remains `0c32be3117d31830c5c2e4a8554b2c2f627ed7474c81dbc1697511e5afbf3b9a`.
No RVDB changes were required. Qualification covers the installed Linux environment;
it does not claim distribution packaging or other operating-system qualification.

Requested repeat verification: `retest/nes/report.json`, `retest/snes/report.json`,
and `retest/genesis/report.json` each passed a 20-second run, Stop/shutdown,
persistent-config preservation and complete transient cleanup. Fresh visual
acceptance remains unconfirmed; process success alone does not establish it.
