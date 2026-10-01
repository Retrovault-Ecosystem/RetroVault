"""Filesystem prerequisites only: package qualification and execution are later gates."""
import os
from pathlib import Path
import shutil

from services.retroarch.core_resolver import CoreResolver, usable_core_file


def executable_path(command):
    if not isinstance(command, str) or not command.strip():
        return None
    command = os.path.expanduser(command.strip())
    try:
        path = (shutil.which(command) if not os.path.dirname(command) else command)
        return path if path and Path(path).is_file() and os.access(path, os.X_OK) else None
    except (OSError, ValueError):
        return None


class LaunchValidator:
    def __init__(self, retroarch, core):
        self.retroarch = retroarch
        self.core = core

    def validate(self, rom, *, platform_id=None):
        results = {"retroarch": self.check_retroarch(), "core": self.check_core(), "rom": self.check_rom(rom)}
        reasons = []
        if not results["retroarch"]:
            reasons.append("RetroArch executable is missing or not executable.")
        if not results["core"]:
            reasons.append("Required core is missing, empty, unreadable, or unsupported on this host.")
        if platform_id:
            selection = CoreResolver.selection(self.core, platform_id)
            if selection.status != "selected":
                results["core"] = False
                reasons.append(selection.message)
        if not results["rom"]:
            reasons.append("ROM file is missing, empty, or unreadable.")
        results["ready"] = all(results.values())
        results["reasons"] = reasons
        return results

    def check_retroarch(self):
        return executable_path(self.retroarch) is not None

    def check_core(self):
        return usable_core_file(self.core)

    def check_rom(self, rom):
        try:
            return bool(rom and Path(rom).is_file() and Path(rom).stat().st_size > 0 and os.access(rom, os.R_OK))
        except (OSError, TypeError, ValueError):
            return False
