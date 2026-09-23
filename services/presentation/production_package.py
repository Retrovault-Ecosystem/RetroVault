from dataclasses import dataclass
from pathlib import Path

from services.presentation.platform_policy import (
    PlatformPresentationPolicyRegistry,
    PlatformPresentationPolicyState,
)


@dataclass(frozen=True)
class ProductionPresentationPackage:
    """
    Validated production-presentation package selected for launch.

    Physical geometry remains owned by the package's runtime descriptor.
    This object only proves that the canonical platform, policy state,
    overlay, shader, runtime descriptor, and production manifest form
    one coherent package before launch side effects begin.
    """

    platform_id: str
    overlay: str
    shader: str
    runtime_descriptor: str
    production_manifest: str


class ProductionPresentationPackageValidator:
    """
    Validate canonical production presentation readiness.

    Legacy callers that do not provide a canonical string platform
    identity remain outside this authority boundary.

    READY canonical platforms must supply one coherent production
    package. UNCONFIGURED canonical platforms fail closed rather than
    borrowing another platform's presentation assets.
    """

    @staticmethod
    def _normalized_string(value):
        if not isinstance(value, str):
            return None

        value = value.strip()

        return value or None

    @classmethod
    def validate(
        cls,
        *,
        platform_id=None,
        core_identity=None,
        overlay=None,
        shader=None,
    ):
        platform_id = cls._normalized_string(
            platform_id
        )

        if platform_id is None:
            return None

        state = (
            PlatformPresentationPolicyRegistry
            .state_for(platform_id)
        )

        if state is None:
            # Preserve the existing unknown-platform discovery/fallback
            # contract. Unknown identities do not become production
            # package assertions.
            return None

        if (
            state
            is PlatformPresentationPolicyState.UNCONFIGURED
        ):
            raise ValueError(
                "RetroVault production presentation is not "
                f"configured for {platform_id}."
            )

        # Resolve the policy first. This proves that a READY platform
        # cannot pair with another platform's registered core policy.
        PlatformPresentationPolicyRegistry.resolve(
            platform_id=platform_id,
            core_identity=core_identity,
        )

        overlay = cls._normalized_string(
            overlay
        )
        shader = cls._normalized_string(
            shader
        )

        if overlay is None:
            raise ValueError(
                "READY platform is missing its production overlay."
            )

        if shader is None:
            raise ValueError(
                "READY platform is missing its production shader."
            )

        overlay_path = (
            Path(overlay)
            .expanduser()
            .resolve(strict=False)
        )

        shader_path = (
            Path(shader)
            .expanduser()
            .resolve(strict=False)
        )

        if not overlay_path.is_file():
            raise ValueError(
                "Production overlay does not exist: "
                f"{overlay_path}"
            )

        if not shader_path.is_file():
            raise ValueError(
                "Production shader does not exist: "
                f"{shader_path}"
            )

        # A production package is intentionally directory-coherent.
        # This prevents a READY platform from combining an overlay from
        # one system/package with a shader from another.
        if overlay_path.parent != shader_path.parent:
            raise ValueError(
                "Production overlay and shader do not belong "
                "to the same package."
            )

        if overlay_path.suffix != ".cfg":
            raise ValueError(
                "Production overlay must be a RetroArch "
                "overlay configuration."
            )

        package_stem = overlay_path.stem

        runtime_descriptor = (
            overlay_path.with_name(
                f"{package_stem}.runtime.cfg"
            )
        )

        production_manifest = (
            overlay_path.with_name(
                f"{package_stem}.production.json"
            )
        )

        if not runtime_descriptor.is_file():
            raise ValueError(
                "Production package is missing its runtime "
                f"descriptor: {runtime_descriptor}"
            )

        if not production_manifest.is_file():
            raise ValueError(
                "Production package is missing its production "
                f"manifest: {production_manifest}"
            )

        # The package path itself must carry the canonical platform
        # identity. This is generic: platform.nintendo.nes -> nes,
        # platform.sega.genesis -> genesis, etc. No launcher branch is
        # added for any individual system.
        platform_token = (
            platform_id
            .rsplit(".", 1)[-1]
            .strip()
            .lower()
        )

        path_parts = {
            part.lower()
            for part in overlay_path.parts
        }

        if platform_token not in path_parts:
            raise ValueError(
                "Production package does not match canonical "
                f"platform identity: {platform_id}"
            )

        return ProductionPresentationPackage(
            platform_id=platform_id,
            overlay=str(overlay_path),
            shader=str(shader_path),
            runtime_descriptor=str(
                runtime_descriptor
            ),
            production_manifest=str(
                production_manifest
            ),
        )
