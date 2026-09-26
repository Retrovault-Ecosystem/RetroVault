from dataclasses import dataclass
import json
from pathlib import Path

from services.presentation.master_profile import (
    MasterPresentationClass,
    MasterPresentationProfile,
    PresentationFitPolicy,
)


@dataclass(frozen=True)
class ProductionGlass:
    """
    Semantic fixed artwork aperture owned by one production package.

    This is system/package presentation metadata.  It is deliberately
    independent of ROM identity, title identity, source raster, and the
    reusable master-profile safe envelope.
    """

    canvas_width: int
    canvas_height: int
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self):
        values = (
            self.canvas_width,
            self.canvas_height,
            self.x,
            self.y,
            self.width,
            self.height,
        )

        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            for value in values
        ):
            raise ValueError(
                "Production glass geometry must contain integers."
            )

        if self.canvas_width <= 0 or self.canvas_height <= 0:
            raise ValueError(
                "Production glass canvas must be positive."
            )

        if self.x < 0 or self.y < 0:
            raise ValueError(
                "Production glass origin cannot be negative."
            )

        if self.width <= 0 or self.height <= 0:
            raise ValueError(
                "Production glass dimensions must be positive."
            )

        if self.x + self.width > self.canvas_width:
            raise ValueError(
                "Production glass exceeds canvas width."
            )

        if self.y + self.height > self.canvas_height:
            raise ValueError(
                "Production glass exceeds canvas height."
            )

    def as_master_profile(
        self,
        *,
        profile_class,
    ) -> MasterPresentationProfile:
        """
        Adapt the fixed package aperture to the existing CONTAIN engine.

        The returned MasterPresentationProfile is an adapter only.  Its
        envelope represents this package's artwork glass, not the generic
        platform-class safe envelope.
        """
        if not isinstance(
            profile_class,
            MasterPresentationClass,
        ):
            raise ValueError(
                "Production glass requires a master presentation class."
            )

        return MasterPresentationProfile(
            profile_class=profile_class,
            canvas_width=self.canvas_width,
            canvas_height=self.canvas_height,
            envelope_x=self.x,
            envelope_y=self.y,
            envelope_width=self.width,
            envelope_height=self.height,
            fit_policy=PresentationFitPolicy.CONTAIN,
        )


class ProductionGlassResolver:
    """
    Resolve semantic fixed-glass authority from a validated production
    manifest.

    Production manifests own artwork aperture metadata.  Runtime CFG files
    remain RetroArch emission artifacts and are not reparsed here as the
    semantic source of package geometry.
    """

    @staticmethod
    def _positive_int(
        value,
        *,
        field,
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value <= 0
        ):
            raise ValueError(
                f"{field} must be a positive integer."
            )

        return value

    @staticmethod
    def _nonnegative_int(
        value,
        *,
        field,
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            raise ValueError(
                f"{field} must be a non-negative integer."
            )

        return value

    @classmethod
    def from_manifest(
        cls,
        production_manifest,
        *,
        expected_platform_id=None,
    ) -> ProductionGlass:
        if not isinstance(
            production_manifest,
            str,
        ):
            raise ValueError(
                "Production manifest path must be a string."
            )

        production_manifest = (
            production_manifest.strip()
        )

        if not production_manifest:
            raise ValueError(
                "Production manifest path cannot be empty."
            )

        path = (
            Path(production_manifest)
            .expanduser()
            .resolve(strict=False)
        )

        if not path.is_file():
            raise ValueError(
                "Production manifest does not exist: "
                f"{path}"
            )

        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8",
                )
            )
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ValueError(
                "Production manifest is unreadable or invalid."
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "Production manifest must contain a JSON object."
            )

        platform_id = data.get(
            "platform_id"
        )

        if (
            not isinstance(platform_id, str)
            or not platform_id.strip()
        ):
            raise ValueError(
                "Production manifest must declare platform_id."
            )

        platform_id = platform_id.strip()

        if expected_platform_id is not None:
            if (
                not isinstance(
                    expected_platform_id,
                    str,
                )
                or not expected_platform_id.strip()
            ):
                raise ValueError(
                    "Expected platform identity must be a non-empty string."
                )

            if (
                platform_id
                != expected_platform_id.strip()
            ):
                raise ValueError(
                    "Production manifest platform identity does not "
                    "match the requested platform."
                )

        canvas = data.get(
            "canvas"
        )

        if not isinstance(canvas, dict):
            raise ValueError(
                "Production manifest must declare canvas geometry."
            )

        aperture = data.get(
            "aperture"
        )

        if not isinstance(aperture, dict):
            raise ValueError(
                "Production manifest must declare aperture geometry."
            )

        canvas_width = cls._positive_int(
            canvas.get("width"),
            field="canvas.width",
        )
        canvas_height = cls._positive_int(
            canvas.get("height"),
            field="canvas.height",
        )

        x = cls._nonnegative_int(
            aperture.get("x"),
            field="aperture.x",
        )
        y = cls._nonnegative_int(
            aperture.get("y"),
            field="aperture.y",
        )
        width = cls._positive_int(
            aperture.get("width"),
            field="aperture.width",
        )
        height = cls._positive_int(
            aperture.get("height"),
            field="aperture.height",
        )

        return ProductionGlass(
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            x=x,
            y=y,
            width=width,
            height=height,
        )
