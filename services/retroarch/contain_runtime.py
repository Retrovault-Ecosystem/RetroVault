from config.paths import runtime_directory
import atexit
import os
import tempfile
from pathlib import Path

from services.presentation.master_profile import (
    MasterPresentationProfile,
)

from .display_aspect import CoreDisplayAspect


def _default_runtime_directory() -> Path:
    return runtime_directory("contain-runtime")


class ContainRuntimeConfig:
    """
    Generate a transient RetroArch custom-viewport layer from one
    reusable presentation envelope and one resolved display aspect.

    This boundary deliberately knows nothing about:

        - game identity;
        - ROM filename;
        - archive member;
        - title-screen state;
        - gameplay state;
        - source raster identity.

    The fixed presentation envelope remains artwork/package authority.
    The supplied display aspect remains emulator/core authority.

    RetroVault performs proportional CONTAIN between those two authorities.
    RetroArch remains the sole owner of final viewport geometry.
    """

    def __init__(
        self,
        directory=None,
    ):
        self.directory = Path(
            directory
            if directory is not None
            else _default_runtime_directory()
        ).expanduser()

        self._created = []

        atexit.register(
            self.cleanup
        )

    @staticmethod
    def _positive_number(
        value,
        *,
        name,
    ):
        if (
            isinstance(value, bool)
            or not isinstance(
                value,
                (int, float),
            )
            or value <= 0
        ):
            raise ValueError(
                f"{name} must be a positive number."
            )

        return value

    @classmethod
    def geometry(
        cls,
        *,
        profile,
        display_aspect_width,
        display_aspect_height,
    ):
        if not isinstance(
            profile,
            MasterPresentationProfile,
        ):
            raise TypeError(
                "profile must be a "
                "MasterPresentationProfile."
            )

        display_aspect_width = (
            cls._positive_number(
                display_aspect_width,
                name="display_aspect_width",
            )
        )

        display_aspect_height = (
            cls._positive_number(
                display_aspect_height,
                name="display_aspect_height",
            )
        )

        return profile.contain_aspect(
            display_aspect_width,
            display_aspect_height,
        )

    def create_for_aspect(
        self,
        *,
        profile,
        display_aspect,
    ):
        if not isinstance(
            display_aspect,
            CoreDisplayAspect,
        ):
            raise TypeError(
                "display_aspect must be a CoreDisplayAspect."
            )

        return self.create(
            profile=profile,
            display_aspect_width=(
                display_aspect.width
            ),
            display_aspect_height=(
                display_aspect.height
            ),
        )

    def create(
        self,
        *,
        profile,
        display_aspect_width,
        display_aspect_height,
    ):
        geometry = self.geometry(
            profile=profile,
            display_aspect_width=(
                display_aspect_width
            ),
            display_aspect_height=(
                display_aspect_height
            ),
        )

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Geometry already contains absolute top-left canvas coordinates.
        # RetroArch adds bias * unused canvas space to custom X/Y; a
        # centering bias here would translate the viewport a second time.
        payload = (
            'aspect_ratio_index = "23"\n'
            'video_force_aspect = "true"\n'
            'video_scale_integer = "false"\n'
            'video_viewport_bias_x = "0.000000"\n'
            'video_viewport_bias_y = "0.000000"\n'
            f'custom_viewport_x = "{geometry.x}"\n'
            f'custom_viewport_y = "{geometry.y}"\n'
            f'custom_viewport_width = "{geometry.width}"\n'
            f'custom_viewport_height = "{geometry.height}"\n'
            'video_crop_overscan = "false"\n'
        )

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="contain-",
            suffix=".cfg",
            dir=self.directory,
            delete=False,
        ) as handle:
            self._created.append(Path(handle.name))
            handle.write(
                payload
            )
            handle.flush()
            os.fsync(
                handle.fileno()
            )

            runtime_file = Path(
                handle.name
            )


        return str(runtime_file)

    def cleanup(
        self,
    ):
        remaining = []

        for path in self._created:
            try:
                path.unlink(
                    missing_ok=True
                )
            except OSError:
                remaining.append(
                    path
                )

        self._created = remaining
