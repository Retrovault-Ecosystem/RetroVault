"""Deterministic local binary resolution; RVDB knowledge is not installation state."""
from dataclasses import dataclass
import os
from pathlib import Path
import sys

from services.retroarch.core_identity import canonical_libretro_core_identity
from services.presentation.platform_policy import PlatformPresentationPolicyRegistry


def core_suffix():
    return {"win32": ".dll", "darwin": ".dylib"}.get(sys.platform, ".so")


def usable_core_file(path):
    try:
        path = Path(path)
        return (path.suffix.casefold() == core_suffix() and path.is_file()
                and path.stat().st_size > 0 and os.access(path, os.R_OK))
    except (OSError, TypeError, ValueError):
        return False


@dataclass(frozen=True)
class CoreResolution:
    status: str
    identity: str = ""
    path: str | None = None
    candidates: tuple[str, ...] = ()
    message: str = ""


class CoreResolver:
    def __init__(self, config):
        self.core_directory = config.get("retroarch", {}).get("cores", {}).get("directory", "")

    @staticmethod
    def selection(name, platform_id=None):
        requested = name.strip() if isinstance(name, str) else ""
        platform_id = platform_id.strip() if isinstance(platform_id, str) else ""
        cores = PlatformPresentationPolicyRegistry.compatible_core_identities(platform_id)
        if platform_id and not cores:
            return CoreResolution("no_policy", message=f"No local core policy is configured for {platform_id}.")
        if not requested:
            if len(cores) == 1:
                requested = cores[0]
            elif cores:
                return CoreResolution("selection_required", candidates=cores,
                                      message="Select an eligible core: " + ", ".join(cores))
            else:
                return CoreResolution("no_policy", message="No emulator core is selected.")
        try:
            identity = canonical_libretro_core_identity(requested)
        except ValueError as exc:
            return CoreResolution("invalid", message=str(exc))
        if platform_id and identity not in cores:
            return CoreResolution("incompatible", identity, message=f"Core {identity} is not eligible for {platform_id}.")
        return CoreResolution("selected", identity)

    def resolve(self, name, platform_id=None):
        selection = self.selection(name, platform_id)
        if selection.status != "selected":
            return selection
        identity = selection.identity
        requested = name.strip() if isinstance(name, str) else ""
        explicit = bool(requested and ("/" in requested or "\\" in requested or requested.startswith("~")))
        try:
            if explicit:
                path = Path(requested).expanduser().absolute()
                if not usable_core_file(path):
                    return CoreResolution("unusable", identity, message=f"Core file is missing, empty, unreadable, or unsupported: {path}")
                return CoreResolution("resolved", identity, str(path), (str(path),))
            if not self.core_directory:
                return CoreResolution("missing", identity, message="No core directory is configured.")
            directory = Path(self.core_directory).expanduser()
            if not directory.is_dir() or not os.access(directory, os.R_OK | os.X_OK):
                return CoreResolution("unusable", identity, message=f"Core directory is unavailable: {directory}")
            matches, unusable = {}, []
            def scan_error(error):
                raise error
            for root, dirs, files in os.walk(directory, onerror=scan_error):
                dirs.sort()
                for filename in sorted(files):
                    if Path(filename).suffix.casefold() != core_suffix():
                        continue
                    if canonical_libretro_core_identity(filename) != identity:
                        continue
                    path = Path(root, filename).absolute()
                    if usable_core_file(path):
                        # Deduplicate aliases while retaining a semantically named
                        # path for the launch profile and package policy checks.
                        matches.setdefault(str(path.resolve()), str(path))
                    else:
                        unusable.append(str(path))
            candidates = tuple(sorted(matches.values()))
            if len(candidates) > 1:
                return CoreResolution("ambiguous", identity, candidates=candidates,
                                      message=f"Multiple installations match core {identity}: " + ", ".join(candidates))
            if candidates:
                return CoreResolution("resolved", identity, candidates[0], candidates)
            if unusable:
                return CoreResolution("unusable", identity, candidates=tuple(unusable),
                                      message=f"Installed core {identity} is empty or unreadable.")
            return CoreResolution("missing", identity, message=f"Required core {identity} is not installed.")
        except (OSError, TypeError, ValueError) as exc:
            return CoreResolution("unusable", identity, message=f"Cannot inspect core installation: {exc}")

    def find(self, name):
        return self.resolve(name).path

    @staticmethod
    def contains_core(directory):
        try:
            path = Path(directory).expanduser()
            if not directory or not path.is_dir() or not os.access(path, os.R_OK | os.X_OK):
                return False
            def scan_error(error):
                raise error
            return any(usable_core_file(Path(root, file))
                       for root, _, files in os.walk(path, onerror=scan_error)
                       for file in files if file.casefold().endswith("_libretro" + core_suffix()))
        except (OSError, TypeError, ValueError):
            return False
