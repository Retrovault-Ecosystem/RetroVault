from config.paths import cache_home
"""Disposable archive classification cache; never used to validate launches."""
import json
import os
import tempfile
from pathlib import Path


class ArchiveScanCache:
    VERSION = 1

    def __init__(self, path=None):
        cache_root = cache_home()
        self.path = Path(path) if path is not None else cache_root / "retrovault/archive-scan.json"
        self.entries = {}
        self.dirty = False
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("version") == self.VERSION and isinstance(data.get("entries"), dict):
                self.entries = data["entries"]
        except (OSError, ValueError, AttributeError):
            pass

    @staticmethod
    def _signature(path):
        stat = path.stat()
        return [stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns]

    def preferred_member(self, archive, runtime):
        path = Path(archive).expanduser().resolve()
        try:
            signature = self._signature(path)
        except OSError:
            return runtime.preferred_member(archive)
        key = str(path)
        entry = self.entries.get(key)
        if (isinstance(entry, dict) and entry.get("signature") == signature
                and isinstance(entry.get("member"), str) and entry["member"]):
            return entry["member"]
        member = runtime.preferred_member(archive)
        # Missing tools, unreadable archives, or an archive being changed
        # during inspection must be retried, rather than cached as failures.
        try:
            unchanged = self._signature(path) == signature
        except OSError:
            unchanged = False
        if isinstance(member, str) and member and unchanged:
            self.entries[key] = {"signature": signature, "member": member}
            self.dirty = True
        return member

    def flush(self):
        if not self.dirty:
            return
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                             dir=self.path.parent, delete=False) as handle:
                temporary = Path(handle.name)
                json.dump({"version": self.VERSION, "entries": self.entries}, handle)
            os.replace(temporary, self.path)
            self.dirty = False
        except OSError:
            # Cache availability must never prevent library discovery.
            pass
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
