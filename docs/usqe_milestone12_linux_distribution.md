# USQE Milestone #12 — Reproducible Linux distribution and acceptance

Status: **COMPLETE within the approved Ubuntu user-local distribution scope.**
Approved target: **Ubuntu 26.04 x86-64, Python 3.14**, versioned user-local release.
This qualifies an isolated fresh application installation on the current host;
it is not evidence from a separately provisioned OS image or another distribution.
RetroArch, cores, ROMs and optional native Snes9x remain external prerequisites.

## Release contract

`scripts/linux_release.py` provides explicit build, install/upgrade, rollback and
remove commands. A deterministic archive carries application source/resources,
pinned offline wheels, the pinned RVDB bundle, exact payload hashes and target/
producer/source provenance. Git commit and dirty-tree status are recorded; hashes
identify actual packaged bytes. No ROMs, personal configuration, saves, development
virtual environment or build-cache files are packaged. Python itself and system
GUI libraries are host prerequisites, not bundled wheels.

Installation verifies the independently obtained archive SHA-256 and exact inventory,
rejects traversal/links, creates a new version-specific environment from offline
wheels, and performs isolated startup and offscreen window checks before changing
one atomic state file. Upgrade uses the same command with a new release ID. Previous
versions are retained. A small root launcher resolves the current version. Existing
XDG configuration/data paths retain their established application meaning.

Rollback verifies the prior version before selecting it. It clears the previous
pointer, rather than automatically toggling forward again. Removal verifies managed
release payloads, deletes managed versions/launcher/state, and retains the ownership
marker and lock for safe retry. It never visits user XDG roots, ROM folders or external
emulator installations. Unknown or modified payloads block removal rather than
being silently deleted. Do not store personal files inside the dedicated release root.
Close RetroVault and its emulator before upgrade, rollback or removal; these commands
do not claim detection/control of independently started application processes.

## Build and use

Run from the checkout with its Python environment. Choose a trusted RVDB producer
commit/hash and a unique release identifier. Download the exact dependency wheels
once on the selected target, then build/install without network access:

```sh
.venv/bin/python -m pip download --only-binary=:all: -r requirements.txt --dest build/release-wheels
.venv/bin/python -m scripts.linux_release build --repo . \
  --bundle data/rvdb/rvdb.bundle.json --bundle-sha APPROVED_BUNDLE_SHA256 \
  --producer-commit APPROVED_RVDB_COMMIT --wheels build/release-wheels \
  --release RELEASE_ID --output build/retrovault-RELEASE_ID.tar.gz
python3 scripts/linux_release.py install build/retrovault-RELEASE_ID.tar.gz \
  --sha256 APPROVED_ARCHIVE_SHA256 --root "$HOME/.local/opt/retrovault"
"$HOME/.local/opt/retrovault/retrovault"
python3 scripts/linux_release.py rollback --root "$HOME/.local/opt/retrovault"
python3 scripts/linux_release.py remove --root "$HOME/.local/opt/retrovault"
```

The release manager's install/rollback/remove paths require only the host standard
library. Python's venv support must be installed. The installer does not use sudo,
install OS packages, download emulators, or modify desktop menus. For an upgrade,
install a new archive/release ID into the same root. Retain the approved archive
and checksum separately. Hashes detect differences but are not signatures.

Use the existing Settings to configure emulator/core/source locations. Bundled
presentation assets remain available to existing deployment services; no production
asset deployment or geometry calibration is performed by installation. A clean
Library is expected until sources are configured. No personal paths are defaults.

## Evidence and limitations

Regression-first archive tests initially failed because the manager did not exist.
Focused tests cover deterministic bytes, checksum rejection, unsafe archive paths,
failed preparation preserving the prior state, rollback/removal with user data
preserved, and rejection of nonempty unowned installation roots.

Fresh offline installation `usqe12-a` and upgrade `usqe12-b` succeeded in
`build/usqe12/installed`, each using newly created virtual environments and isolated
startup profiles. Identical-input archive rebuilds were byte-identical. These are
candidate artifacts with honest dirty-tree provenance. Final source publication and
an artifact rebuilt from the published checkpoint are separate steps.

The first visible-acceptance wrapper incorrectly passed an argument to Qt's static
exec method. It failed in test orchestration, not application initialization; the
corrected wrapper's result is recorded separately. No production code was altered.

No claim of byte-identical generated virtual environments, universal host support,
OS-image reproducibility, power-loss durability, signing, automatic updates or
system package-manager integration is made. A killed installer may leave an inactive
version directory; it does not select it. A duplicate release ID is refused rather
than overwritten. Modified bundle files from later explicit RVDB updates cause
release verification to refuse rollback/removal until reviewed; no automatic repair
or destructive overwrite is provided. Existing app persistence formats are unchanged;
future incompatible versions would need their own migration/rollback qualification.


## Final qualification and closure

The user accepted the visible packaged application: “Yes, the packaged application
looks and works correctly”. Corrected desktop acceptance exited 0. Actual isolated
installation, offline upgrade, verified rollback and removal passed; all seven
files in the isolated acceptance user profile were preserved. Real user data was
not modified. Logs and checksums remain under `build/usqe12/`.

Full RetroVault suite: **2,516 passed**; full RVDB suite: **407 passed**. Focused
release checks: **7 passed**. Source validation: **59 valid entities**, zero schema
and relationship errors. Canonical/installed RVDB parity and all 39 protected
asset/core/bundle checksums are unchanged. Compilation and whitespace checks pass.
Bundle SHA-256: `4d99f2b1bff694f26ca1b1ff68b7d4d1816236abb1e64d10a62e14bf20e3eb43`.

The user authorized committing/pushing Milestone #12, followed by an audit of all
12 milestones. The closure commit contains the manager, tests and instructions;
archive payloads and downloaded wheels are local build artifacts, not Git source.
The final archive is to be rebuilt from the clean published source checkpoint and
its exact SHA-256 retained in the local release receipt. No hosted binary-release
upload or claim of new platform/controller qualification is implied.
