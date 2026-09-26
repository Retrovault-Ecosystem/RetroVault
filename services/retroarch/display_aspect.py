from dataclasses import dataclass


@dataclass(frozen=True)
class CoreDisplayAspect:
    """
    Emulator/core-authoritative display shape.

    This object deliberately contains no content identity and no source
    raster dimensions.  It is only the intended display proportion that
    presentation code may CONTAIN inside a reusable fixed envelope.
    """

    width: float
    height: float

    def __post_init__(self):
        for name, value in (
            ("width", self.width),
            ("height", self.height),
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

    @property
    def ratio(self):
        return self.width / self.height

    @classmethod
    def from_launch_profile(
        cls,
        profile,
    ):
        width = getattr(
            profile,
            "display_aspect_width",
            None,
        )

        height = getattr(
            profile,
            "display_aspect_height",
            None,
        )

        if width is None and height is None:
            return None

        if width is None or height is None:
            raise ValueError(
                "Display aspect requires both width and height."
            )

        return cls(
            width=width,
            height=height,
        )
