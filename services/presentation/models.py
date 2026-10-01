from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .production_package import ProductionPresentationPackage


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


@dataclass(frozen=True)
class LaunchPresentation:
    """Read-only decision; saved intent is distinct from launch authority."""

    requested: PresentationProfile
    selected: PresentationProfile
    sources: tuple[tuple[str, str], ...] = ()
    authority: str = "manual"
    package: ProductionPresentationPackage | None = None
    error: str = ""
    visual_tuning: tuple[tuple[str, float | None], ...] = ()

    @property
    def available(self):
        return not self.error
