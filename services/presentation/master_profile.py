from dataclasses import dataclass
from enum import Enum


class MasterPresentationClass(str, Enum):
    """
    Reusable RetroVault physical-presentation classes.

    A class describes the glass/envelope available to authentic content.
    It never describes an individual game or ROM.
    """

    CLASSIC_4_3 = "classic_4_3"
    WIDESCREEN_16_9 = "widescreen_16_9"
    ARCADE_VERTICAL = "arcade_vertical"
    ARCADE_HORIZONTAL = "arcade_horizontal"
    HANDHELD_NATIVE = "handheld_native"
    DUAL_SCREEN = "dual_screen"
    SPECIALIZED = "specialized"


class PresentationFitPolicy(str, Enum):
    """
    Rules governing placement of authentic content inside an envelope.
    """

    CONTAIN = "contain"


class MasterPresentationQualification(str, Enum):
    """
    Qualification state for reusable presentation capability classes.

    QUALIFIED means a reusable physical envelope currently exists.

    CAPABILITY_ONLY means the family is recognized architecturally but
    physical geometry must not be guessed. Platform/core evidence and
    validation are required before a production envelope is assigned.
    """

    QUALIFIED = "qualified"
    CAPABILITY_ONLY = "capability_only"


@dataclass(frozen=True)
class MasterPresentationProfile:
    """
    Immutable physical presentation contract.

    Canvas:
        Complete RetroVault presentation surface.

    Envelope:
        Maximum glass area available to the authentic game image.

    CONTAIN means:

        - preserve the intended display aspect ratio;
        - scale proportionally;
        - never exceed the envelope;
        - never crop merely to fill artwork;
        - never stretch merely to fill artwork;
        - center unused space unless a future reusable profile
          deliberately specifies another alignment.

    This object contains no title, ROM, archive, or game identity.
    """

    profile_class: MasterPresentationClass

    canvas_width: int
    canvas_height: int

    envelope_x: int
    envelope_y: int
    envelope_width: int
    envelope_height: int

    fit_policy: PresentationFitPolicy = (
        PresentationFitPolicy.CONTAIN
    )

    def __post_init__(self):
        numeric = {
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "envelope_x": self.envelope_x,
            "envelope_y": self.envelope_y,
            "envelope_width": self.envelope_width,
            "envelope_height": self.envelope_height,
        }

        for name, value in numeric.items():
            if not isinstance(value, int):
                raise TypeError(
                    f"{name} must be an integer."
                )

        if self.canvas_width <= 0:
            raise ValueError(
                "Canvas width must be positive."
            )

        if self.canvas_height <= 0:
            raise ValueError(
                "Canvas height must be positive."
            )

        if self.envelope_width <= 0:
            raise ValueError(
                "Envelope width must be positive."
            )

        if self.envelope_height <= 0:
            raise ValueError(
                "Envelope height must be positive."
            )

        if self.envelope_x < 0:
            raise ValueError(
                "Envelope X cannot be negative."
            )

        if self.envelope_y < 0:
            raise ValueError(
                "Envelope Y cannot be negative."
            )

        if (
            self.envelope_x
            + self.envelope_width
            > self.canvas_width
        ):
            raise ValueError(
                "Envelope exceeds canvas width."
            )

        if (
            self.envelope_y
            + self.envelope_height
            > self.canvas_height
        ):
            raise ValueError(
                "Envelope exceeds canvas height."
            )

    @property
    def canvas(self):
        return (
            self.canvas_width,
            self.canvas_height,
        )

    @property
    def envelope(self):
        return (
            self.envelope_x,
            self.envelope_y,
            self.envelope_width,
            self.envelope_height,
        )

    def contain_aspect(
        self,
        display_aspect_width,
        display_aspect_height,
    ):
        """
        Contain a resolved display aspect inside this profile envelope.

        Inputs describe intended DISPLAY proportions, not necessarily
        raw framebuffer dimensions. This preserves the distinction
        required for systems with non-square pixel aspect ratios.

        The result preserves display aspect, never exceeds the glass
        envelope, never crops to satisfy artwork, never stretches to
        fill unused glass, and remains centered.
        """
        for name, value in (
            (
                "display_aspect_width",
                display_aspect_width,
            ),
            (
                "display_aspect_height",
                display_aspect_height,
            ),
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

        scale = min(
            self.envelope_width
            / display_aspect_width,
            self.envelope_height
            / display_aspect_height,
        )

        width = max(
            1,
            min(
                self.envelope_width,
                round(
                    display_aspect_width
                    * scale
                ),
            ),
        )

        height = max(
            1,
            min(
                self.envelope_height,
                round(
                    display_aspect_height
                    * scale
                ),
            ),
        )

        x = (
            self.envelope_x
            + (
                self.envelope_width
                - width
            )
            // 2
        )

        y = (
            self.envelope_y
            + (
                self.envelope_height
                - height
            )
            // 2
        )

        return ContainedPresentationGeometry(
            x=x,
            y=y,
            width=width,
            height=height,
        )

    def contain(
        self,
        source_width,
        source_height,
    ):
        """
        Calculate a centered proportional fit inside this profile.

        The result is integer physical geometry suitable for a
        presentation backend such as RetroArch.

        No source pixels are deliberately discarded by this operation.
        """

        for name, value in (
            ("source_width", source_width),
            ("source_height", source_height),
        ):
            if not isinstance(value, int):
                raise TypeError(
                    f"{name} must be an integer."
                )

            if value <= 0:
                raise ValueError(
                    f"{name} must be positive."
                )

        width_scale = (
            self.envelope_width
            / source_width
        )

        height_scale = (
            self.envelope_height
            / source_height
        )

        scale = min(
            width_scale,
            height_scale,
        )

        width = min(
            self.envelope_width,
            max(
                1,
                round(
                    source_width
                    * scale
                ),
            ),
        )

        height = min(
            self.envelope_height,
            max(
                1,
                round(
                    source_height
                    * scale
                ),
            ),
        )

        x = (
            self.envelope_x
            + (
                self.envelope_width
                - width
            )
            // 2
        )

        y = (
            self.envelope_y
            + (
                self.envelope_height
                - height
            )
            // 2
        )

        return ContainedPresentationGeometry(
            x=x,
            y=y,
            width=width,
            height=height,
        )


@dataclass(frozen=True)
class ContainedPresentationGeometry:
    """
    Calculated physical placement of authentic content.
    """

    x: int
    y: int
    width: int
    height: int


MASTER_PRESENTATION_QUALIFICATION = {
    MasterPresentationClass.CLASSIC_4_3:
        MasterPresentationQualification.QUALIFIED,
    MasterPresentationClass.WIDESCREEN_16_9:
        MasterPresentationQualification.QUALIFIED,
    MasterPresentationClass.ARCADE_VERTICAL:
        MasterPresentationQualification.QUALIFIED,

    # Recognized reusable families whose exact physical geometry is not
    # yet qualified. No platform receives these classes automatically.
    MasterPresentationClass.ARCADE_HORIZONTAL:
        MasterPresentationQualification.CAPABILITY_ONLY,
    MasterPresentationClass.HANDHELD_NATIVE:
        MasterPresentationQualification.CAPABILITY_ONLY,
    MasterPresentationClass.DUAL_SCREEN:
        MasterPresentationQualification.CAPABILITY_ONLY,
    MasterPresentationClass.SPECIALIZED:
        MasterPresentationQualification.CAPABILITY_ONLY,
}


def master_presentation_qualification(profile_class):
    if isinstance(profile_class, str):
        try:
            profile_class = MasterPresentationClass(
                profile_class
            )
        except ValueError as exc:
            raise KeyError(profile_class) from exc

    try:
        return MASTER_PRESENTATION_QUALIFICATION[
            profile_class
        ]
    except KeyError as exc:
        raise KeyError(profile_class) from exc


def master_presentation_class_is_physically_qualified(
    profile_class,
):
    return (
        master_presentation_qualification(
            profile_class
        )
        is MasterPresentationQualification.QUALIFIED
    )


class MasterPresentationProfileRegistry:
    """
    Canonical RetroVault master-presentation authority.

    These profiles are reusable presentation classes.

    They are intentionally independent from:

        - game identity;
        - ROM filename;
        - archive filename;
        - emulator framebuffer dimensions;
        - system-specific artwork.

    System/platform policy may select one of these profiles.
    """

    _PROFILES = {
        MasterPresentationClass.CLASSIC_4_3: (
            MasterPresentationProfile(
                profile_class=(
                    MasterPresentationClass
                    .CLASSIC_4_3
                ),
                canvas_width=1920,
                canvas_height=1080,
                envelope_x=240,
                envelope_y=0,
                envelope_width=1440,
                envelope_height=1080,
            )
        ),
        MasterPresentationClass.WIDESCREEN_16_9: (
            MasterPresentationProfile(
                profile_class=(
                    MasterPresentationClass
                    .WIDESCREEN_16_9
                ),
                canvas_width=1920,
                canvas_height=1080,
                envelope_x=0,
                envelope_y=0,
                envelope_width=1920,
                envelope_height=1080,
            )
        ),
        MasterPresentationClass.ARCADE_VERTICAL: (
            MasterPresentationProfile(
                profile_class=(
                    MasterPresentationClass
                    .ARCADE_VERTICAL
                ),
                canvas_width=1920,
                canvas_height=1080,
                envelope_x=656,
                envelope_y=0,
                envelope_width=608,
                envelope_height=1080,
            )
        ),
    }

    @classmethod
    def get(
        cls,
        profile_class,
    ):
        if isinstance(
            profile_class,
            str,
        ):
            try:
                profile_class = (
                    MasterPresentationClass(
                        profile_class
                    )
                )
            except ValueError:
                return None

        return cls._PROFILES.get(
            profile_class
        )

    @classmethod
    def require(
        cls,
        profile_class,
    ):
        profile = cls.get(
            profile_class
        )

        if profile is None:
            raise ValueError(
                "Unknown RetroVault master "
                "presentation profile."
            )

        return profile

    @classmethod
    def all(cls):
        return tuple(
            cls._PROFILES.values()
        )
