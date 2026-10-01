from dataclasses import dataclass
from pathlib import Path
from config import ConfigLoader

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
                "retrovault/nes/classic/RetroVault_NES_Classic.cfg"
            ),
            shader=(
                "retrovault/nes/classic/"
                "RetroVault_NES_Classic_CRT.slangp"
            ),
        ),
        "platform.nintendo.snes": CanonicalProductionPackageAssets(
            overlay=(
                "retrovault/snes/classic/RetroVault_SNES_Classic.cfg"
            ),
            shader=(
                "retrovault/snes/classic/"
                "RetroVault_SNES_Classic_CRT.slangp"
            ),
        ),
        "platform.sega.genesis": CanonicalProductionPackageAssets(
            overlay=(
                "retrovault/genesis/classic/"
                "RetroVault_Genesis_Classic.cfg"
            ),
            shader=(
                "retrovault/genesis/classic/"
                "RetroVault_Genesis_Classic_CRT.slangp"
            ),
        ),
    }

    @classmethod
    def resolve(
        cls,
        *,
        platform_id,
        core_identity,
        config=None,
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

        config = ConfigLoader().load() if config is None else config
        if not isinstance(config, dict) or not isinstance(config.get("paths", {}), dict):
            raise ValueError("Presentation configuration must contain a paths mapping.")
        paths = config.get("paths", {})
        def installed(kind, relative):
            entry = paths.get(kind, {})
            if not isinstance(entry, dict):
                raise ValueError(f"Presentation directory configuration for {kind} must be a mapping.")
            root = entry.get("directory", "")
            if not isinstance(root, str) or not root.strip():
                raise ValueError(f"No local presentation asset root configured for {kind}.")
            root = Path(root).expanduser().resolve()
            candidate = (root / relative).resolve()
            try:
                candidate.relative_to(root)
            except ValueError as exc:
                raise ValueError(f"Production {kind} asset escapes its configured root.") from exc
            return str(candidate)
        overlay = installed("overlays", assets.overlay)
        shader = installed("shaders", assets.shader)

        return ProductionPresentationPackageValidator.validate(
            platform_id=platform_id,
            core_identity=core_identity,
            overlay=overlay,
            shader=shader,
        )
