import json
from dataclasses import dataclass
from pathlib import Path

from services.presentation.platform_policy import (
    PlatformPresentationPolicyRegistry,
    PlatformPresentationPolicyState,
)
from services.presentation.production_glass import (
    ProductionGlassResolver,
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

    def fixed_glass(self):
        """
        Return this package's semantic fixed artwork aperture.

        The production manifest is the package-level source of aperture
        authority.  Callers do not need to parse RetroArch runtime CFG
        syntax or substitute the generic master safe envelope.
        """
        return ProductionGlassResolver.from_manifest(
            self.production_manifest,
            expected_platform_id=self.platform_id,
        )


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

        # Production package identity is semantic, not positional.
        # The manifest must explicitly declare the exact canonical
        # RVDB platform ID asserted by the launch boundary.
        try:
            manifest_data = json.loads(
                production_manifest.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ValueError(
                "RetroVault production presentation manifest "
                "is unreadable or invalid."
            ) from exc

        if not isinstance(
            manifest_data,
            dict,
        ):
            raise ValueError(
                "RetroVault production presentation manifest "
                "must contain a JSON object."
            )

        manifest_platform_id = (
            manifest_data.get(
                "platform_id"
            )
        )

        if not isinstance(
            manifest_platform_id,
            str,
        ):
            raise ValueError(
                "RetroVault production presentation manifest "
                "does not declare canonical platform identity."
            )

        manifest_platform_id = (
            manifest_platform_id.strip()
        )

        if (
            manifest_platform_id
            != platform_id
        ):
            raise ValueError(
                "RetroVault production presentation manifest "
                "platform identity does not match the launch "
                "platform."
            )

        # Production package identity is semantic rather than
        # positional. RetroVault deliberately deploys overlays and
        # shaders beneath independent configured roots, so requiring
        # both files to share one filesystem parent rejects the normal
        # production topology.
        #
        # When the production manifest explicitly declares its CRT
        # preset, that declaration is the authoritative shader member
        # of the package. Only the basename is compared because the
        # deployment root is intentionally independent.
        production_assets = manifest_data.get(
            "production_assets"
        )

        declared_shader = None

        if isinstance(
            production_assets,
            dict,
        ):
            value = production_assets.get(
                "crt_preset"
            )

            if isinstance(
                value,
                str,
            ):
                value = value.strip()

                if value:
                    declared_shader = Path(
                        value
                    ).name

        if declared_shader is not None:
            if shader_path.name != declared_shader:
                raise ValueError(
                    "Production overlay and shader do not belong "
                    "to the same package."
                )
        else:
            # Older production manifests may predate the explicit
            # production_assets contract. Preserve fail-closed package
            # mixing protection by requiring the overlay descriptor and
            # shader preset to share the canonical package stem.
            overlay_stem = overlay_path.stem
            shader_stem = shader_path.stem

            accepted_shader_stems = {
                overlay_stem,
                f"{overlay_stem}_CRT",
            }

            if shader_stem not in accepted_shader_stems:
                raise ValueError(
                    "Production overlay and shader do not belong "
                    "to the same package."
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
