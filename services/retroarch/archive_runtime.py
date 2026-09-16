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

    def playable_members(self, rom):
        source = (
            Path(rom)
            .expanduser()
            .resolve()
        )

        if (
            source.suffix.lower()
            not in self.ARCHIVE_EXTENSIONS
        ):
            return []

        if not source.is_file():
            return []

        if self.executable is None:
            return []

        members = self._list_members(
            source
        )

        return [
            member
            for member in members
            if (
                self._member_is_safe(member)
                and Path(member)
                .suffix
                .lower()
                in self.PLAYABLE_EXTENSIONS
            )
        ]

    def preferred_member(self, rom):
        source = (
            Path(rom)
            .expanduser()
            .resolve()
        )

        playable = self.playable_members(
            source
        )

        if not playable:
            return None

        return self._select_member(
            source,
            playable,
        )

    def resolve(
        self,
        rom,
        member=None,
    ):
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
                self._member_is_safe(member)
                and Path(member)
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

        if member:
            if not self._member_is_safe(
                member
            ):
                raise ValueError(
                    "Selected archive member has "
                    f"an unsafe path: {member}"
                )

            if member not in playable:
                raise ValueError(
                    "Selected archive member is not "
                    f"playable or is not present: {member}"
                )
        else:
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

    @staticmethod
    def _member_is_safe(member):
        """
        Accept only relative archive-member paths that remain beneath
        the extraction destination.

        Archive listings are untrusted input. Reject parent traversal,
        absolute POSIX paths, Windows drive paths, UNC paths, and their
        backslash-separated equivalents before a member can participate
        in selection or extraction.
        """
        if not isinstance(member, str):
            return False

        value = member.strip()

        if not value:
            return False

        normalized = value.replace("\\", "/")

        if normalized.startswith("/"):
            return False

        if normalized.startswith("//"):
            return False

        if (
            len(normalized) >= 2
            and normalized[0].isalpha()
            and normalized[1] == ":"
        ):
            return False

        parts = normalized.split("/")

        if any(part == ".." for part in parts):
            return False

        return True

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

        ranked = sorted(
            playable,
            key=lambda member: (
                self._member_rank(
                    source,
                    member,
                ),
                Path(member).name.casefold(),
                member.casefold(),
            ),
        )

        return ranked[0]

    @staticmethod
    def _member_rank(
        source,
        member,
    ):
        """
        Deterministically select the preferred playable member
        from GoodSet-style multi-ROM archives.

        Preference order:
        1. Good dump marker [!]
        2. Verified/common region releases
        3. Non-beta/non-prototype/non-hack/non-bad dumps
        4. Stable lexical ordering as final tie-break
        """

        name = (
            Path(member)
            .name
            .casefold()
        )

        score = 1000

        if "[!]" in name:
            score -= 500

        preferred_regions = (
            "(u)",
            "(usa)",
            "(e)",
            "(europe)",
            "(j)",
            "(japan)",
            "(w)",
            "(world)",
        )

        for index, marker in enumerate(
            preferred_regions
        ):
            if marker in name:
                score -= (
                    100
                    - index
                )
                break

        undesirable = (
            "[b",
            "[h",
            "[t",
            "[o",
            "[p",
            "(beta",
            "(proto",
            "(prototype",
            "(sample",
            "(demo",
            "(hack",
            "(pirate",
        )

        for marker in undesirable:
            if marker in name:
                score += 250

        archive_name = (
            source.stem
            .casefold()
        )

        member_stem = (
            Path(member)
            .stem
            .casefold()
        )

        if member_stem.startswith(
            archive_name
        ):
            score -= 25

        return score

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
