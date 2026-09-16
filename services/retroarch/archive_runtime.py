import hashlib
import shutil
import subprocess
from pathlib import Path


class ArchiveRuntime:
    """
    Resolve launchable content from supported compressed archives.

    The original archive remains the durable RetroVault Library identity.
    Extracted content is transient runtime material stored beneath the
    RetroVault cache.
    """

    ARCHIVE_EXTENSIONS = {
        ".7z",
    }

    PLAYABLE_EXTENSIONS = {
        ".nes",
        ".sfc",
        ".smc",
        ".bin",
        ".gen",
        ".md",
        ".chd",
        ".iso",
        ".cue",
        ".z64",
        ".n64",
        ".v64",
    }

    def __init__(
        self,
        cache_root=None,
        executable=None,
    ):
        self.cache_root = Path(
            cache_root
            if cache_root is not None
            else (
                Path.home()
                / ".cache"
                / "retrovault"
                / "archive-runtime"
            )
        )

        self.executable = (
            executable
            if executable is not None
            else (
                shutil.which("7z")
                or shutil.which("7za")
            )
        )

    def resolve(self, rom):
        source = (
            Path(rom)
            .expanduser()
            .resolve()
        )

        if (
            source.suffix.lower()
            not in self.ARCHIVE_EXTENSIONS
        ):
            return str(source)

        if not source.is_file():
            raise ValueError(
                f"Archive does not exist: {source}"
            )

        if self.executable is None:
            raise ValueError(
                "7-Zip executable was not found."
            )

        members = self._list_members(
            source
        )

        playable = [
            member
            for member in members
            if (
                Path(member)
                .suffix
                .lower()
                in self.PLAYABLE_EXTENSIONS
            )
        ]

        if not playable:
            raise ValueError(
                "Archive contains no supported "
                f"ROM content: {source.name}"
            )

        member = self._select_member(
            source,
            playable,
        )

        destination = self._destination(
            source
        )

        extracted = (
            destination
            / member
        )

        if (
            extracted.is_file()
            and extracted.stat().st_size > 0
        ):
            return str(
                extracted.resolve()
            )

        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        result = subprocess.run(
            [
                self.executable,
                "x",
                "-y",
                f"-o{destination}",
                str(source),
                member,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise ValueError(
                "Unable to extract archive "
                f"{source.name}: "
                f"{result.stderr.strip() or result.stdout.strip()}"
            )

        if (
            not extracted.is_file()
            or extracted.stat().st_size <= 0
        ):
            raise ValueError(
                "Archive extraction did not produce "
                f"the expected ROM: {member}"
            )

        return str(
            extracted.resolve()
        )

    def _list_members(
        self,
        source,
    ):
        result = subprocess.run(
            [
                self.executable,
                "l",
                "-slt",
                str(source),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise ValueError(
                "Unable to inspect archive "
                f"{source.name}: "
                f"{result.stderr.strip() or result.stdout.strip()}"
            )

        members = []

        for line in result.stdout.splitlines():
            if not line.startswith("Path = "):
                continue

            value = line[
                len("Path = "):
            ].strip()

            if not value:
                continue

            members.append(
                value
            )

        source_text = str(source)

        return [
            member
            for member in members
            if member != source_text
        ]

    def _select_member(
        self,
        source,
        playable,
    ):
        if len(playable) == 1:
            return playable[0]

        archive_stem = (
            source.stem
            .casefold()
        )

        exact = [
            member
            for member in playable
            if (
                Path(member)
                .stem
                .casefold()
                == archive_stem
            )
        ]

        if len(exact) == 1:
            return exact[0]

        raise ValueError(
            "Archive contains multiple supported "
            "ROM files and RetroVault cannot safely "
            "choose one automatically: "
            f"{source.name}"
        )

    def _destination(
        self,
        source,
    ):
        stat = source.stat()

        identity = (
            f"{source}|"
            f"{stat.st_size}|"
            f"{stat.st_mtime_ns}"
        )

        digest = hashlib.sha256(
            identity.encode(
                "utf-8"
            )
        ).hexdigest()[:24]

        return (
            self.cache_root
            / digest
        )
