import os
import re
from pathlib import Path

from .display_aspect import CoreDisplayAspect


class RuntimeDisplayAspectObserver:
    """
    Incrementally observe libretro display-aspect authority from a
    RetroArch verbose log without reading from the emulator process.

    RetroArch emits two relevant records:

      [Core] Geometry: WIDTHxHEIGHT, Aspect: ASPECT
      [Environ] SET_GEOMETRY: WIDTHxHEIGHT, Aspect: ASPECT

    The initial Core Geometry record establishes the first observed
    display aspect.  Every subsequent valid SET_GEOMETRY record
    supersedes it.  This mirrors libretro's runtime geometry authority:
    the latest valid geometry is authoritative.

    The reported display aspect is primary.  WIDTH/HEIGHT is only the
    libretro fallback when the reported aspect is non-positive.

    This observer is deliberately content-independent.  It does not
    inspect ROM names, titles, platform-specific raster tables, or
    game state.

    poll() performs only an incremental regular-file read.  It never
    waits on, communicates with, or reads stdout/stderr from the
    emulator process.
    """

    _GEOMETRY_RE = re.compile(
        r"""
        \[Core\]\s+
        Geometry:\s*
        (?P<width>\d+)
        x
        (?P<height>\d+)
        ,\s*
        Aspect:\s*
        (?P<aspect>
            [-+]?
            (?:\d+(?:\.\d*)?|\.\d+)
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    _SET_GEOMETRY_RE = re.compile(
        r"""
        \[Environ\]\s+
        SET_GEOMETRY:\s*
        (?P<width>\d+)
        x
        (?P<height>\d+)
        ,\s*
        Aspect:\s*
        (?P<aspect>
            [-+]?
            (?:\d+(?:\.\d*)?|\.\d+)
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    def __init__(self, log_path):
        if not isinstance(
            log_path,
            (str, os.PathLike),
        ):
            raise TypeError(
                "log_path must be a filesystem path."
            )

        self._log_path = Path(log_path)
        self._offset = 0
        self._pending = ""
        self._display_aspect = None
        self._initial_geometry_seen = False
        self._set_geometry_count = 0

    @property
    def log_path(self) -> Path:
        return self._log_path

    @property
    def display_aspect(self):
        return self._display_aspect

    @property
    def initial_geometry_seen(self) -> bool:
        return self._initial_geometry_seen

    @property
    def set_geometry_count(self) -> int:
        return self._set_geometry_count

    def reset(self) -> None:
        self._offset = 0
        self._pending = ""
        self._display_aspect = None
        self._initial_geometry_seen = False
        self._set_geometry_count = 0

    @staticmethod
    def _resolved_aspect(
        *,
        width,
        height,
        aspect,
    ):
        try:
            width = int(width)
            height = int(height)
            aspect = float(aspect)
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return None

        if width <= 0 or height <= 0:
            return None

        if aspect > 0:
            return CoreDisplayAspect(
                width=aspect,
                height=1.0,
            )

        return CoreDisplayAspect(
            width=float(width),
            height=float(height),
        )

    def _observe_line(self, line: str):
        set_geometry = (
            self._SET_GEOMETRY_RE.search(line)
        )

        if set_geometry is not None:
            aspect = self._resolved_aspect(
                width=set_geometry.group("width"),
                height=set_geometry.group("height"),
                aspect=set_geometry.group("aspect"),
            )

            if aspect is not None:
                self._display_aspect = aspect
                self._set_geometry_count += 1

            return self._display_aspect

        geometry = self._GEOMETRY_RE.search(line)

        if geometry is None:
            return self._display_aspect

        aspect = self._resolved_aspect(
            width=geometry.group("width"),
            height=geometry.group("height"),
            aspect=geometry.group("aspect"),
        )

        if aspect is None:
            return self._display_aspect

        self._initial_geometry_seen = True

        # A late/repeated Core Geometry diagnostic must never roll back
        # authority after a legitimate runtime SET_GEOMETRY transition.
        if self._set_geometry_count == 0:
            self._display_aspect = aspect

        return self._display_aspect

    def observe_text(self, text: str):
        if not isinstance(text, str):
            raise TypeError(
                "Runtime geometry evidence must be text."
            )

        for line in text.splitlines():
            self._observe_line(line)

        return self._display_aspect

    def poll(self):
        """
        Read only bytes appended since the previous poll.

        A partial final line is retained until its newline arrives.
        If the log is replaced or truncated, observation restarts from
        the beginning of the new file.
        """

        try:
            size = self._log_path.stat().st_size
        except FileNotFoundError:
            return self._display_aspect

        if size < self._offset:
            self.reset()

        try:
            with self._log_path.open(
                "r",
                encoding="utf-8",
                errors="replace",
            ) as handle:
                handle.seek(self._offset)
                chunk = handle.read()
                self._offset = handle.tell()
        except FileNotFoundError:
            return self._display_aspect

        if not chunk:
            return self._display_aspect

        text = self._pending + chunk

        if text.endswith("\n"):
            complete = text
            self._pending = ""
        else:
            complete, separator, pending = (
                text.rpartition("\n")
            )

            if separator:
                complete += separator
                self._pending = pending
            else:
                self._pending = text
                complete = ""

        if complete:
            self.observe_text(complete)

        return self._display_aspect
