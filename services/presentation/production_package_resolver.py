from dataclasses import dataclass
from pathlib import Path

from services.presentation.platform_policy import (
    PlatformPresentationPolicyRegistry,
    PlatformPresentationPolicyState,
)
from services.presentation.production_package import (
    ProductionPresentationPackage,
    ProductionPresentationPackageValidator,
)


@dataclass(frozen=True)
class CanonicalProductionPackageAssets:
    """
    Canonical deployed production assets for one READY platform.

    This resolver deliberately contains no game, ROM, title, archive-member,
    raster, or screen-state authority. READY package selection is platform
    authoritative.
    """

    overlay: str
    shader: str


class CanonicalProductionPackageResolver:
    _ASSETS = {
        "platform.nintendo.nes": CanonicalProductionPackageAssets(
            overlay=(
                "/opt/retropie/configs/all/retroarch/overlays/"
                "retrovault/nes/classic/RetroVault_NES_Classic.cfg"
            ),
            shader=(
                "/opt/retropie/configs/all/retroarch/shaders/"
                "retrovault/nes/classic/"
                "RetroVault_NES_Classic_CRT.slangp"
            ),
        ),
        "platform.nintendo.snes": CanonicalProductionPackageAssets(
            overlay=(
                "/opt/retropie/configs/all/retroarch/overlays/"
                "retrovault/snes/classic/RetroVault_SNES_Classic.cfg"
            ),
            shader=(
                "/opt/retropie/configs/all/retroarch/shaders/"
                "retrovault/snes/classic/"
                "RetroVault_SNES_Classic_CRT.slangp"
            ),
        ),
    }

    @classmethod
    def resolve(
        cls,
        *,
        platform_id,
        core_identity,
    ):
        if not isinstance(platform_id, str):
            return None

        platform_id = platform_id.strip()

        if not platform_id:
            return None

        state = PlatformPresentationPolicyRegistry.state_for(
            platform_id
        )

        if state is None:
            return None

        if state is PlatformPresentationPolicyState.UNCONFIGURED:
            raise ValueError(
                "RetroVault production presentation is not "
                f"configured for {platform_id}."
            )

        if state is not PlatformPresentationPolicyState.READY:
            return None

        try:
            assets = cls._ASSETS[platform_id]
        except KeyError as exc:
            raise ValueError(
                "READY platform has no canonical RetroVault "
                f"production package mapping: {platform_id}."
            ) from exc

        overlay = str(
            Path(assets.overlay).expanduser().resolve(strict=False)
        )
        shader = str(
            Path(assets.shader).expanduser().resolve(strict=False)
        )

        return ProductionPresentationPackageValidator.validate(
            platform_id=platform_id,
            core_identity=core_identity,
            overlay=overlay,
            shader=shader,
        )
