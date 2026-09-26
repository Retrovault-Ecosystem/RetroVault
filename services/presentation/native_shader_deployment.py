import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .visual_catalog import (
    VisualAsset,
    VisualAssetSource,
    VisualAssetType,
)


_PRESET_EXTENSIONS = {
    ".cgp",
    ".glslp",
    ".slangp",
}

_SHADER_EXTENSIONS = {
    ".cg",
    ".glsl",
    ".slang",
}

_DEPENDENCY_EXTENSIONS = (
    _PRESET_EXTENSIONS
    | _SHADER_EXTENSIONS
)

_SHADER_ASSIGNMENT_REFERENCE = re.compile(
    r"""^\s*shader\d+\s*=\s*["']([^"']+)["']\s*$""",
    flags=(
        re.MULTILINE
        | re.IGNORECASE
    ),
)

_REFERENCE_DIRECTIVE = re.compile(
    r"""^\s*#reference\s+(?:"([^"]+)"|'([^']+)'|(\S+))\s*$""",
    flags=(
        re.MULTILINE
        | re.IGNORECASE
    ),
)


@dataclass(frozen=True)
class NativeShaderDeployment:
    """
    Deterministic deployment plan for one RVV-native shader preset.

    relative_preset is rooted beneath RetroVault's portable shader
    namespace. source_files and relative_files preserve dependency
    topology exactly when copied into the configured RetroArch shader
    root.
    """

    asset_id: str
    relative_preset: Path
    source_preset: Path
    source_files: tuple[Path, ...]
    relative_files: tuple[Path, ...]
    shader_root: Path
    destination_preset: Path

    @property
    def portable_reference(self):
        return (
            "retro-vault://shaders/"
            + self.relative_preset.as_posix()
        )


class NativeShaderDeploymentService:
    """
    Deploy explicitly cataloged RVV-native shader presets.

    This authority is intentionally separate from native overlay
    deployment. Static shader/preset references are traversed
    recursively and copied while preserving repository-relative
    topology beneath RetroVault's shader package root.

    Deployment does not own presentation assignment, platform policy,
    launch behavior, physical geometry, or per-content decisions.
    """

    PORTABLE_PREFIX = "retro-vault://shaders/"

    def __init__(
        self,
        *,
        repository_root,
        shader_root,
    ):
        self.repository_root = Path(
            repository_root
        ).expanduser().resolve()

        self.shader_root = Path(
            shader_root
        ).expanduser().resolve()

        self.package_root = (
            self.repository_root
            / "retrovault"
        ).resolve()

    @staticmethod
    def _require_native_shader(
        asset,
    ):
        if not isinstance(
            asset,
            VisualAsset,
        ):
            raise TypeError(
                "Native RVV shader deployment "
                "requires a VisualAsset."
            )

        if (
            asset.source
            is not VisualAssetSource.RVV_NATIVE
        ):
            raise ValueError(
                "Only RVV-native shader assets "
                "may use native shader deployment."
            )

        if (
            asset.asset_type
            is not VisualAssetType.SHADER
        ):
            raise ValueError(
                "Native RVV shader deployment "
                "supports shader assets only."
            )

        if not asset.reference.startswith(
            NativeShaderDeploymentService
            .PORTABLE_PREFIX
        ):
            raise ValueError(
                "Native RVV shader must use a "
                "portable shader reference."
            )

    @staticmethod
    def _safe_relative_path(
        value,
    ):
        path = Path(value)

        if path.is_absolute():
            raise ValueError(
                "Native RVV shader deployment "
                "path must be relative."
            )

        if not path.parts:
            raise ValueError(
                "Native RVV shader deployment "
                "path must not be empty."
            )

        if any(
            part in ("", ".", "..")
            for part in path.parts
        ):
            raise ValueError(
                "Native RVV shader deployment "
                "path contains unsafe components."
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
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError(
                message
            ) from exc

    def _relative_preset(
        self,
        asset,
    ):
        value = asset.reference[
            len(self.PORTABLE_PREFIX):
        ]

        relative = self._safe_relative_path(
            value
        )

        if (
            relative.suffix.casefold()
            not in _PRESET_EXTENSIONS
        ):
            raise ValueError(
                "Native RVV shader reference "
                "must identify a supported preset."
            )

        return relative

    def _source_preset(
        self,
        relative_preset,
    ):
        source = (
            self.package_root
            / relative_preset
        ).resolve()

        self._assert_within(
            source,
            self.package_root,
            message=(
                "Native RVV shader source escaped "
                "the repository package root."
            ),
        )

        if not source.is_file():
            raise ValueError(
                "Native RVV shader preset does "
                f"not exist: {source}"
            )

        return source

    @staticmethod
    def _contains_runtime_token(
        reference,
    ):
        start = 0

        while True:
            opening = reference.find(
                "$",
                start,
            )

            if opening < 0:
                return False

            closing = reference.find(
                "$",
                opening + 1,
            )

            if closing < 0:
                return False

            token = reference[
                opening + 1:closing
            ]

            if (
                token
                and all(
                    character.isalnum()
                    or character in "_-"
                    for character in token
                )
            ):
                return True

            start = closing + 1

    @staticmethod
    def _static_references(
        preset,
    ):
        text = preset.read_text(
            encoding="utf-8",
            errors="replace",
        )

        references = []

        for line in text.splitlines():
            stripped = line.strip()

            if not stripped:
                continue

            reference_match = (
                _REFERENCE_DIRECTIVE.match(
                    line
                )
            )

            if reference_match:
                value = next(
                    item
                    for item
                    in reference_match.groups()
                    if item is not None
                )
            else:
                shader_match = (
                    _SHADER_ASSIGNMENT_REFERENCE
                    .match(
                        line
                    )
                )

                if not shader_match:
                    continue

                value = (
                    shader_match.group(1)
                )

            value = value.replace(
                "\\\\",
                "/",
            )

            if (
                NativeShaderDeploymentService
                ._contains_runtime_token(
                    value
                )
            ):
                raise ValueError(
                    "RVV-native shader dependencies "
                    "must be statically resolvable; "
                    f"runtime token found: {value}"
                )

            references.append(
                value
            )

        return tuple(
            references
        )

    def _resolve_dependency(
        self,
        owner,
        reference,
    ):
        reference_path = Path(
            reference
        ).expanduser()

        if reference_path.is_absolute():
            raise ValueError(
                "RVV-native shader dependencies "
                "must use portable relative references."
            )

        if (
            reference_path.suffix.casefold()
            not in _DEPENDENCY_EXTENSIONS
        ):
            raise ValueError(
                "Native RVV shader dependency "
                "uses an unsupported file type."
            )

        candidate = (
            owner.parent
            / reference_path
        ).resolve()

        try:
            candidate.relative_to(
                self.package_root
            )
        except ValueError:
            return self._resolve_external_dependency(
                owner,
                reference_path,
            )

        if not candidate.is_file():
            raise ValueError(
                "Native RVV shader dependency "
                f"does not exist: {candidate}"
            )

        return candidate

    def _resolve_external_dependency(
        self,
        owner,
        reference_path,
    ):
        owner_relative = owner.relative_to(
            self.package_root
        )

        deployed_owner = (
            self.shader_root
            / "retrovault"
            / owner_relative
        ).resolve()

        candidate = (
            deployed_owner.parent
            / reference_path
        ).resolve()

        self._assert_within(
            candidate,
            self.shader_root,
            message=(
                "Native RVV shader external dependency "
                "escaped the configured shader root."
            ),
        )

        if not candidate.is_file():
            raise ValueError(
                "Native RVV shader external dependency "
                f"does not exist: {candidate}"
            )

        return candidate

    def _dependency_closure(
        self,
        source_preset,
    ):
        pending = [
            source_preset
        ]

        discovered = {}

        while pending:
            current = pending.pop()

            relative = current.relative_to(
                self.package_root
            )

            if relative in discovered:
                continue

            discovered[
                relative
            ] = current

            if (
                current.suffix.casefold()
                not in _PRESET_EXTENSIONS
            ):
                continue

            for reference in self._static_references(
                current
            ):
                dependency = (
                    self._resolve_dependency(
                        current,
                        reference,
                    )
                )

                try:
                    dependency_relative = (
                        dependency.relative_to(
                            self.package_root
                        )
                    )
                except ValueError:
                    # Installed third-party shader dependencies are
                    # validated beneath the configured shader root,
                    # but remain externally owned and are not copied.
                    continue

                if (
                    dependency_relative
                    not in discovered
                ):
                    pending.append(
                        dependency
                    )

        ordered = tuple(
            sorted(
                discovered.items(),
                key=lambda item: (
                    item[0].as_posix().casefold()
                ),
            )
        )

        return (
            tuple(
                source
                for _, source in ordered
            ),
            tuple(
                relative
                for relative, _ in ordered
            ),
        )

    def plan(
        self,
        asset,
    ):
        self._require_native_shader(
            asset
        )

        relative_preset = (
            self._relative_preset(
                asset
            )
        )

        source_preset = (
            self._source_preset(
                relative_preset
            )
        )

        (
            source_files,
            relative_files,
        ) = self._dependency_closure(
            source_preset
        )

        destination_preset = (
            self.shader_root
            / "retrovault"
            / relative_preset
        ).resolve()

        self._assert_within(
            destination_preset,
            self.shader_root,
            message=(
                "Native RVV shader destination "
                "escaped the configured shader root."
            ),
        )

        return NativeShaderDeployment(
            asset_id=asset.id,
            relative_preset=relative_preset,
            source_preset=source_preset,
            source_files=source_files,
            relative_files=relative_files,
            shader_root=self.shader_root,
            destination_preset=destination_preset,
        )

    @staticmethod
    def _copy_to_staging(
        source,
        destination,
    ):
        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

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

    @staticmethod
    def _remove_empty_parents(
        path,
        *,
        stop,
    ):
        current = path

        while current != stop:
            try:
                current.rmdir()
            except OSError:
                break

            current = current.parent

    def deploy(
        self,
        asset,
    ):
        plan = self.plan(
            asset
        )

        parent = self.shader_root.parent

        parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        token = asset.id.replace(
            "/",
            "_",
        )

        staging = (
            parent
            / (
                ".retrovault-shader-staging-"
                + token
            )
        )

        backup = (
            parent
            / (
                ".retrovault-shader-backup-"
                + token
            )
        )

        self._remove_tree(
            staging
        )
        self._remove_tree(
            backup
        )

        staging.mkdir(
            parents=True
        )

        existing = set()
        installed = []

        try:
            for source, relative in zip(
                plan.source_files,
                plan.relative_files,
            ):
                self._copy_to_staging(
                    source,
                    staging / relative,
                )

            for source, relative in zip(
                plan.source_files,
                plan.relative_files,
            ):
                staged = (
                    staging
                    / relative
                )

                if (
                    staged.read_bytes()
                    != source.read_bytes()
                ):
                    raise RuntimeError(
                        "Native RVV shader staging "
                        "verification failed."
                    )

            if self.shader_root.exists():
                if not self.shader_root.is_dir():
                    raise ValueError(
                        "Configured shader root "
                        "must be a directory."
                    )
            else:
                self.shader_root.mkdir(
                    parents=True,
                    exist_ok=True,
                )

            backup.mkdir(
                parents=True,
                exist_ok=True,
            )

            for relative in plan.relative_files:
                destination = (
                    self.shader_root
                    / "retrovault"
                    / relative
                ).resolve()

                self._assert_within(
                    destination,
                    self.shader_root,
                    message=(
                        "Native RVV shader "
                        "destination escaped the "
                        "configured shader root."
                    ),
                )

                if destination.exists():
                    if not destination.is_file():
                        raise ValueError(
                            "Native RVV shader "
                            "destination must be "
                            "a regular file."
                        )

                    existing.add(
                        relative
                    )

                    backup_file = (
                        backup
                        / relative
                    )

                    self._copy_to_staging(
                        destination,
                        backup_file,
                    )

                destination.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

            for relative in plan.relative_files:
                staged = (
                    staging
                    / relative
                )

                destination = (
                    self.shader_root
                    / "retrovault"
                    / relative
                ).resolve()

                os.replace(
                    staged,
                    destination,
                )

                installed.append(
                    relative
                )

            for source, relative in zip(
                plan.source_files,
                plan.relative_files,
            ):
                destination = (
                    self.shader_root
                    / "retrovault"
                    / relative
                )

                if (
                    not destination.is_file()
                    or destination.read_bytes()
                    != source.read_bytes()
                ):
                    raise RuntimeError(
                        "Native RVV shader deployment "
                        "verification failed."
                    )

        except Exception:
            for relative in reversed(
                installed
            ):
                destination = (
                    self.shader_root
                    / "retrovault"
                    / relative
                )

                if relative in existing:
                    backup_file = (
                        backup
                        / relative
                    )

                    if backup_file.is_file():
                        destination.parent.mkdir(
                            parents=True,
                            exist_ok=True,
                        )

                        os.replace(
                            backup_file,
                            destination,
                        )
                else:
                    if destination.is_file():
                        destination.unlink()

                    self._remove_empty_parents(
                        destination.parent,
                        stop=self.shader_root,
                    )

            self._remove_tree(
                staging
            )
            self._remove_tree(
                backup
            )

            raise

        self._remove_tree(
            staging
        )
        self._remove_tree(
            backup
        )

        return plan
