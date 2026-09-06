from dataclasses import dataclass


@dataclass(frozen=True)
class PresentationProfile:
    """
    Resolved or assignable RetroVault presentation properties.

    Empty fields mean that the assignment does not override the
    corresponding lower-precedence presentation property.
    """

    shader: str = ""
    overlay: str = ""
    artwork: str = ""
