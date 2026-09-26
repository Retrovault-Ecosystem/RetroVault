from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from services.presentation.master_profile import (
    MasterPresentationProfile,
)

from .contain_runtime import ContainRuntimeConfig
from .runtime_display_aspect import (
    RuntimeDisplayAspectObserver,
)


class RuntimePresentationSession:
    """
    Own one isolated RetroArch runtime-observation session.

    The session owns:
      * one private verbose RetroArch log;
      * one RuntimeDisplayAspectObserver;
      * one transient CONTAIN viewport descriptor at a time.

    The fixed glass is supplied as a MasterPresentationProfile and is
    never mutated.  Runtime libretro display aspect determines only the
    inner contained game rectangle.

    No ROM name, title, archive member, game state, or source-raster
    lookup participates in geometry selection.
    """

    def __init__(
        self,
        profile: MasterPresentationProfile,
        *,
        directory=None,
        contain_runtime=None,
    ):
        if not isinstance(
            profile,
            MasterPresentationProfile,
        ):
            raise TypeError(
                "profile must be a MasterPresentationProfile."
            )

        self._profile = profile

        if directory is None:
            self._directory = (
                Path.home()
                / ".cache"
                / "retrovault"
                / "runtime-presentation"
            )
        else:
            self._directory = Path(directory)

        self._contain_runtime = (
            contain_runtime
            if contain_runtime is not None
            else ContainRuntimeConfig(
                directory=self._directory
                / "contain"
            )
        )

        self._session_directory = None
        self._log_path = None
        self._observer = None
        self._contain_path = None
        self._last_ratio = None

    @property
    def profile(self):
        return self._profile

    @property
    def log_path(self):
        if self._log_path is None:
            return None

        return str(self._log_path)

    @property
    def observer(self):
        return self._observer

    @property
    def contain_path(self):
        return self._contain_path

    @property
    def display_aspect(self):
        if self._observer is None:
            return None

        return self._observer.display_aspect

    def create(self):
        if self._session_directory is not None:
            raise RuntimeError(
                "Runtime presentation session is already active."
            )

        self._directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._session_directory = Path(
            tempfile.mkdtemp(
                prefix="session-",
                dir=str(self._directory),
            )
        )

        self._log_path = (
            self._session_directory
            / "retroarch.log"
        )

        self._observer = (
            RuntimeDisplayAspectObserver(
                self._log_path
            )
        )

        return str(self._log_path)

    def poll(self):
        if self._observer is None:
            return None

        aspect = self._observer.poll()

        if aspect is None:
            return None

        ratio = aspect.ratio

        if (
            self._last_ratio is not None
            and abs(
                ratio - self._last_ratio
            ) <= 1e-12
        ):
            return self._contain_path

        self._contain_runtime.cleanup()

        self._contain_path = (
            self._contain_runtime
            .create_for_aspect(
                profile=self._profile,
                display_aspect=aspect,
            )
        )

        self._last_ratio = ratio

        return self._contain_path

    def cleanup(self):
        self._contain_runtime.cleanup()

        if (
            self._session_directory is not None
            and self._session_directory.exists()
        ):
            shutil.rmtree(
                self._session_directory,
                ignore_errors=True,
            )

        self._session_directory = None
        self._log_path = None
        self._observer = None
        self._contain_path = None
        self._last_ratio = None
