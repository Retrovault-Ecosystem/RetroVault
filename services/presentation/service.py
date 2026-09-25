from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from config import ConfigLoader

from .native_deployment import (
    NativeVisualDeployment,
    NativeVisualDeploymentService,
)
from .native_shader_deployment import (
    NativeShaderDeployment,
    NativeShaderDeploymentService,
)
from .visual_catalog import (
    VisualAsset,
    VisualAssetCatalog,
    VisualAssetSource,
    VisualAssetType,
)
from .visual_manifest import (
    VisualAssetCatalogManifest,
)


class NativeVisualInstallStatus(str, Enum):
    """Application-facing native RVV installation state."""

    NOT_INSTALLED = "not_installed"
    CURRENT = "current"
    OUTDATED = "outdated"


@dataclass(frozen=True)
class NativeVisualStatus:
    """Installation status for one cataloged RVV-native visual."""

    asset: VisualAsset
    status: NativeVisualInstallStatus
    deployment: (
        NativeVisualDeployment
        | NativeShaderDeployment
    )


class NativeVisualService:
    """
    Application-facing native RVV visual service.

    This boundary owns:

      - effective RetroVault configuration access
      - native visual catalog access
      - installation-state inspection
      - explicit native visual installation

    It does not own:

      - presentation assignment
      - recommendation precedence
      - generic overlay discovery
      - RetroArch launch behavior
      - user configuration persistence
    """

    def __init__(
        self,
        *,
        repository_root=None,
        config_loader=None,
        catalog_manifest=None,
    ):
        self.repository_root = Path(
            repository_root
            or Path(__file__).resolve().parents[2]
        ).expanduser().resolve()

        self.config_loader = (
            config_loader
            or ConfigLoader()
        )

        self.catalog_manifest = (
            catalog_manifest
            or VisualAssetCatalogManifest()
        )

    def _load_config(self):
        config = self.config_loader.load()

        if not isinstance(config, dict):
            raise ValueError(
                "RetroVault configuration must "
                "contain a mapping."
            )

        return config

    def _configured_visual_root(
        self,
        kind,
    ):
        config = self._load_config()

        try:
            directory = (
                config["paths"][kind]["directory"]
            )
        except (
            KeyError,
            TypeError,
        ) as exc:
            raise ValueError(
                "RetroVault configuration does not "
                f"define paths.{kind}.directory."
            ) from exc

        if (
            not isinstance(
                directory,
                str,
            )
            or not directory.strip()
        ):
            raise ValueError(
                "RetroVault configured "
                f"{kind} directory must be "
                "a non-empty string."
            )

        return Path(
            directory
        ).expanduser().resolve()

    def overlay_root(self):
        return self._configured_visual_root(
            "overlays"
        )

    def shader_root(self):
        return self._configured_visual_root(
            "shaders"
        )

    def catalog(self) -> VisualAssetCatalog:
        return self.catalog_manifest.load()

    def native_assets(self):
        return tuple(
            asset
            for asset in self.catalog().for_source(
                VisualAssetSource.RVV_NATIVE
            )
            if asset.asset_type
            in {
                VisualAssetType.OVERLAY,
                VisualAssetType.SHADER,
            }
        )

    def require_native_asset(
        self,
        asset_id,
    ):
        asset = self.catalog().require(
            asset_id
        )

        if (
            asset.source
            is not VisualAssetSource.RVV_NATIVE
        ):
            raise ValueError(
                "Visual asset is not RVV-native."
            )

        if asset.asset_type not in {
            VisualAssetType.OVERLAY,
            VisualAssetType.SHADER,
        }:
            raise ValueError(
                "Native RVV application service "
                "supports overlay and shader "
                "assets only."
            )

        return asset

    def _deployment_service(
        self,
        asset,
    ):
        if (
            asset.asset_type
            is VisualAssetType.OVERLAY
        ):
            return NativeVisualDeploymentService(
                repository_root=self.repository_root,
                overlay_root=self.overlay_root(),
            )

        if (
            asset.asset_type
            is VisualAssetType.SHADER
        ):
            return NativeShaderDeploymentService(
                repository_root=self.repository_root,
                shader_root=self.shader_root(),
            )

        raise ValueError(
            "Unsupported RVV-native visual "
            "asset type."
        )

    @staticmethod
    def _is_current(
        deployment,
    ):
        if isinstance(
            deployment,
            NativeVisualDeployment,
        ):
            destination = (
                deployment.destination_directory
            )

            if not destination.is_dir():
                return False

            expected_names = {
                source.name
                for source
                in deployment.source_files
            }

            actual_names = {
                path.name
                for path
                in destination.iterdir()
                if path.is_file()
            }

            if actual_names != expected_names:
                return False

            pairs = (
                (
                    source,
                    destination / source.name,
                )
                for source
                in deployment.source_files
            )

        elif isinstance(
            deployment,
            NativeShaderDeployment,
        ):
            pairs = zip(
                deployment.source_files,
                (
                    deployment.shader_root
                    / relative
                    for relative
                    in deployment.relative_files
                ),
            )

        else:
            raise TypeError(
                "Unknown native RVV deployment "
                "type."
            )

        for source, deployed in pairs:
            if not deployed.is_file():
                return False

            try:
                if (
                    deployed.read_bytes()
                    != source.read_bytes()
                ):
                    return False
            except OSError:
                return False

        return True

    def status(
        self,
        asset_id,
    ) -> NativeVisualStatus:
        asset = self.require_native_asset(
            asset_id
        )

        deployment = (
            self._deployment_service(
                asset
            ).plan(
                asset
            )
        )

        if isinstance(
            deployment,
            NativeVisualDeployment,
        ):
            exists = (
                deployment
                .destination_directory
                .exists()
            )
        elif isinstance(
            deployment,
            NativeShaderDeployment,
        ):
            exists = any(
                (
                    deployment.shader_root
                    / relative
                ).exists()
                for relative
                in deployment.relative_files
            )
        else:
            raise TypeError(
                "Unknown native RVV deployment "
                "type."
            )

        if not exists:
            state = (
                NativeVisualInstallStatus
                .NOT_INSTALLED
            )
        elif self._is_current(
            deployment
        ):
            state = (
                NativeVisualInstallStatus
                .CURRENT
            )
        else:
            state = (
                NativeVisualInstallStatus
                .OUTDATED
            )

        return NativeVisualStatus(
            asset=asset,
            status=state,
            deployment=deployment,
        )

    def install(
        self,
        asset_id,
    ) -> NativeVisualStatus:
        asset = self.require_native_asset(
            asset_id
        )

        self._deployment_service(
            asset
        ).deploy(
            asset
        )

        result = self.status(
            asset_id
        )

        if (
            result.status
            is not NativeVisualInstallStatus.CURRENT
        ):
            raise RuntimeError(
                "Native RVV installation did not "
                "reach CURRENT state."
            )

        return result
