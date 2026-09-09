import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from .visual_catalog import (
    VisualAsset,
    VisualAssetSource,
    VisualAssetType,
)


@dataclass(frozen=True)
class NativeVisualDeployment:
    """
    Deterministic deployment plan for one native RVV visual.

    The catalog-relative descriptor is authoritative for both
    repository source identity and configured runtime identity.
    """

    asset_id: str
    relative_descriptor: Path
    source_descriptor: Path
    source_files: tuple[Path, ...]
    overlay_root: Path
    destination_directory: Path
    destination_descriptor: Path

    @property
    def portable_reference(self):
        return (
            "retro-vault://overlays/"
            + self.relative_descriptor.as_posix()
        )


class NativeVisualDeploymentService:
    """
    Deploy explicitly cataloged RVV-native overlay packages.

    Deployment is independent from:

      - presentation assignment
      - recommendation precedence
      - generic overlay discovery
      - generic asset organization
      - RetroArch launch behavior

    Package replacement is transactional at the directory level.
    """

    PORTABLE_PREFIX = "retro-vault://overlays/"

    def __init__(
        self,
        *,
        repository_root,
        overlay_root,
    ):
        self.repository_root = Path(
            repository_root
        ).expanduser().resolve()

        self.overlay_root = Path(
            overlay_root
        ).expanduser().resolve()

    @staticmethod
    def _require_native_overlay(
        asset,
    ):
        if not isinstance(
            asset,
            VisualAsset,
        ):
            raise TypeError(
                "Native RVV deployment requires "
                "a VisualAsset."
            )

        if (
            asset.source
            is not VisualAssetSource.RVV_NATIVE
        ):
            raise ValueError(
                "Only RVV-native visual assets "
                "may use native deployment."
            )

        if (
            asset.asset_type
            is not VisualAssetType.OVERLAY
        ):
            raise ValueError(
                "Native RVV deployment currently "
                "supports overlay assets only."
            )

        if not asset.reference.startswith(
            NativeVisualDeploymentService.PORTABLE_PREFIX
        ):
            raise ValueError(
                "Native RVV overlay must use a "
                "portable overlay reference."
            )

    @staticmethod
    def _safe_relative_path(
        value,
    ):
        path = Path(value)

        if path.is_absolute():
            raise ValueError(
                "Native RVV deployment path "
                "must be relative."
            )

        if not path.parts:
            raise ValueError(
                "Native RVV deployment path "
                "must not be empty."
            )

        if any(
            part in ("", ".", "..")
            for part in path.parts
        ):
            raise ValueError(
                "Native RVV deployment path "
                "contains unsafe components."
            )

        return path

    @staticmethod
    def _assert_within(
        path,
        root,
        *,
        message,
    ):
        try:
            path.relative_to(
                root
            )
        except ValueError as exc:
            raise ValueError(
                message
            ) from exc

    def _destination_relative_descriptor(
        self,
        asset,
    ):
        relative = asset.reference[
            len(self.PORTABLE_PREFIX):
        ]

        return self._safe_relative_path(
            relative
        )

    def _source_descriptor(
        self,
        relative_descriptor,
    ):
        source = (
            self.repository_root
            / relative_descriptor
        ).resolve()

        package_root = (
            self.repository_root
            / "retrovault"
        ).resolve()

        self._assert_within(
            source,
            package_root,
            message=(
                "Native RVV source escaped "
                "the repository package root."
            ),
        )

        if not source.is_file():
            raise ValueError(
                "Native RVV source descriptor "
                f"does not exist: {source}"
            )

        return source

    @staticmethod
    def _overlay_image_reference(
        descriptor,
    ):
        image_reference = None

        for raw_line in descriptor.read_text(
            encoding="utf-8"
        ).splitlines():
            line = raw_line.strip()

            if not line.startswith(
                "overlay0_overlay"
            ):
                continue

            key, separator, value = (
                line.partition("=")
            )

            if (
                not separator
                or key.strip() != "overlay0_overlay"
            ):
                continue

            value = value.strip()

            if (
                len(value) >= 2
                and value[0] == '"'
                and value[-1] == '"'
            ):
                value = value[1:-1]

            image_reference = value
            break

        if not image_reference:
            raise ValueError(
                "Native RVV overlay descriptor "
                "does not define overlay0_overlay."
            )

        return (
            NativeVisualDeploymentService
            ._safe_relative_path(
                image_reference
            )
        )

    def plan(
        self,
        asset,
    ):
        self._require_native_overlay(
            asset
        )

        relative_descriptor = (
            self._destination_relative_descriptor(
                asset
            )
        )

        source_descriptor = (
            self._source_descriptor(
                relative_descriptor
            )
        )

        image_relative = (
            self._overlay_image_reference(
                source_descriptor
            )
        )

        source_package = (
            source_descriptor.parent.resolve()
        )

        source_image = (
            source_package
            / image_relative
        ).resolve()

        self._assert_within(
            source_image,
            source_package,
            message=(
                "Native RVV overlay image escaped "
                "its production package."
            ),
        )

        if not source_image.is_file():
            raise ValueError(
                "Native RVV production image "
                f"does not exist: {source_image}"
            )

        runtime_descriptor = (
            source_descriptor
            .with_suffix(".runtime.cfg")
        )

        shader_descriptor = (
            source_descriptor
            .with_suffix(".shader.cfg")
        )

        source_files = [
            source_descriptor,
            source_image,
        ]

        if runtime_descriptor.exists():
            if not runtime_descriptor.is_file():
                raise ValueError(
                    "Native RVV runtime descriptor "
                    "must be a regular file."
                )

            self._assert_within(
                runtime_descriptor.resolve(),
                source_package,
                message=(
                    "Native RVV runtime descriptor "
                    "escaped its production package."
                ),
            )

            source_files.append(
                runtime_descriptor
            )

        if shader_descriptor.exists():
            if not shader_descriptor.is_file():
                raise ValueError(
                    "Native RVV shader descriptor "
                    "must be a regular file."
                )

            self._assert_within(
                shader_descriptor.resolve(),
                source_package,
                message=(
                    "Native RVV shader descriptor "
                    "escaped its production package."
                ),
            )

            source_files.append(
                shader_descriptor
            )

        destination_descriptor = (
            self.overlay_root
            / relative_descriptor
        ).resolve()

        self._assert_within(
            destination_descriptor,
            self.overlay_root,
            message=(
                "Native RVV destination escaped "
                "the configured overlay root."
            ),
        )

        return NativeVisualDeployment(
            asset_id=asset.id,
            relative_descriptor=(
                relative_descriptor
            ),
            source_descriptor=(
                source_descriptor
            ),
            source_files=tuple(
                source_files
            ),
            overlay_root=(
                self.overlay_root
            ),
            destination_directory=(
                destination_descriptor.parent
            ),
            destination_descriptor=(
                destination_descriptor
            ),
        )

    @staticmethod
    def _copy_to_staging(
        source,
        destination,
    ):
        shutil.copyfile(
            source,
            destination,
        )

        with destination.open(
            "rb"
        ) as handle:
            os.fsync(
                handle.fileno()
            )

    @staticmethod
    def _remove_tree(
        path,
    ):
        if path.exists():
            shutil.rmtree(
                path
            )

    def deploy(
        self,
        asset,
    ):
        plan = self.plan(
            asset
        )

        destination = (
            plan.destination_directory
        )

        parent = destination.parent

        parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        staging = parent / (
            "."
            + destination.name
            + ".retrovault-staging"
        )

        backup = parent / (
            "."
            + destination.name
            + ".retrovault-backup"
        )

        if staging.exists():
            raise ValueError(
                "Native RVV staging directory "
                f"already exists: {staging}"
            )

        if backup.exists():
            raise ValueError(
                "Native RVV backup directory "
                f"already exists: {backup}"
            )

        staging.mkdir()

        old_moved = False

        try:
            for source in plan.source_files:
                target = (
                    staging
                    / source.name
                )

                self._copy_to_staging(
                    source,
                    target,
                )

            for source in plan.source_files:
                staged = (
                    staging
                    / source.name
                )

                if (
                    staged.read_bytes()
                    != source.read_bytes()
                ):
                    raise ValueError(
                        "Native RVV staged file "
                        "failed byte verification."
                    )

            if destination.exists():
                os.replace(
                    destination,
                    backup,
                )

                old_moved = True

            try:
                os.replace(
                    staging,
                    destination,
                )
            except Exception:
                if old_moved:
                    os.replace(
                        backup,
                        destination,
                    )

                    old_moved = False

                raise

            if old_moved:
                self._remove_tree(
                    backup
                )

                old_moved = False

        finally:
            self._remove_tree(
                staging
            )

            if (
                backup.exists()
                and not destination.exists()
            ):
                os.replace(
                    backup,
                    destination,
                )

            elif backup.exists():
                self._remove_tree(
                    backup
                )

        return plan
