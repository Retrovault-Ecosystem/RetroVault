# Startup performance repair — 2026-09-28

The user requested substantially faster `python3 app.py` startup. Profiling the
current library found 3,942 7-Zip invocations before the window appeared (the
same archives were encountered through overlapping sources). Archive inspection
accounted for about 14 of 21 profiled construction seconds.

`ArchiveScanCache` now stores successful preferred-member classifications in the
user's disposable cache. Entries are keyed by resolved archive path and validated
against device, inode, size, mtime_ns, and ctime_ns. Replaced/changed archives are
re-inspected. Failed classifications are retried. Corrupt or unwritable caches
fall back to scanning. Actual launch-time archive validation is unchanged.
A cache schema version allows future selection-rule changes to invalidate entries.
The current library cache was populated during verification. A fresh cache still
requires initial inspection, and filesystem enumeration remains live on each scan.

The unchanged theme is now applied once after the widget tree is constructed,
before showMaximized, avoiding repeated stylesheet work while thousands of
library widgets are being assembled and reparented.

## Matched measurements

Measured in separate processes with the same library, including imports, window
construction, theme application, showMaximized and one event-processing pass.
Qt's offscreen platform isolates startup work from window-manager behavior; these
are local warm-filesystem measurements, not a guarantee of cold-boot timing.
Baseline reproduces the original uncached scanner and early theme application.

| Interpreter | Before | After | Library games |
| --- | ---: | ---: | ---: |
| User's python3 (Python 3.14.4 / Qt 6.10.2) | 18.076 s | 3.205 s | 1,968 |
| Repository venv (Python 3.14.4 / Qt 6.11.0) | 17.861 s | 2.929 s | 1,968 |

User interpreter improvement: approximately 82% less startup time (5.6x faster).
Diagnostic scripts, profiles, and JSON results: `build/startup/` (ignored).

Validation: full suite 1,845 passed; final startup/cache focused checks 7 passed;
`git diff --check` clean. No game-launch or bezel settings changed in this repair.
No commit or push.
