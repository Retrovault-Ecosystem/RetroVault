from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from config import ConfigLoader

from .native_deployment import (
    NativeVisualDeployment,
    NativeVisualDeploymentService,
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
    deployment: NativeVisualDeployment


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

        try:
            overlay_directory = (
                config["paths"]["overlays"]["directory"]
            )
        except (
            KeyError,
            TypeError,
        ) as exc:
            raise ValueError(
                "RetroVault configuration does not "
                "define paths.overlays.directory."
            ) from exc

        if (
            not isinstance(
                overlay_directory,
                str,
            )
            or not overlay_directory.strip()
        ):
            raise ValueError(
                "RetroVault configured overlay "
                "directory must be a non-empty string."
            )

        return config

    def overlay_root(self):
        config = self._load_config()

        return Path(
            config["paths"]["overlays"]["directory"]
        ).expanduser().resolve()

    def catalog(self) -> VisualAssetCatalog:
        return self.catalog_manifest.load()

    def native_assets(self):
        return tuple(
            asset
            for asset in self.catalog().for_source(
                VisualAssetSource.RVV_NATIVE
            )
            if asset.asset_type
            is VisualAssetType.OVERLAY
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

        if (
            asset.asset_type
            is not VisualAssetType.OVERLAY
        ):
            raise ValueError(
                "Native RVV application service "
                "currently supports overlays only."
            )

        return asset

    def _deployment_service(self):
        return NativeVisualDeploymentService(
            repository_root=self.repository_root,
            overlay_root=self.overlay_root(),
        )

    @staticmethod
    def _is_current(
        deployment,
    ):
        destination = (
            deployment.destination_directory
        )

        if not destination.is_dir():
            return False

        expected_names = {
            source.name
            for source in deployment.source_files
        }

        actual_names = {
            path.name
            for path in destination.iterdir()
            if path.is_file()
        }

        if actual_names != expected_names:
            return False

        for source in deployment.source_files:
            deployed = (
                destination
                / source.name
            )

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
            self._deployment_service().plan(
                asset
            )
        )

        if not (
            deployment.destination_directory
            .exists()
        ):
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

        self._deployment_service().deploy(
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
