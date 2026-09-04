import shutil
from pathlib import Path

from .models import (
    AssetExecutionResult,
    AssetMove,
    AssetPackagePlan,
    AssetPackageResult,
    AssetPlan,
)


OVERLAY_IMAGE_EXTENSIONS = {
    ".jpeg",
    ".jpg",
    ".png",
    ".webp",
}

SHADER_EXTENSIONS = {
    ".cg",
    ".cgp",
    ".glsl",
    ".glslp",
    ".slang",
    ".slangp",
}


class AssetOrganizer:
    """Build safe recursive asset move plans."""

    def plan(
        self,
        source_root,
        overlay_directory,
        shader_directory,
    ):
        source = Path(
            source_root
        ).expanduser().resolve(
            strict=False
        )
        overlays = Path(
            overlay_directory
        ).expanduser().resolve(
            strict=False
        )
        shaders = Path(
            shader_directory
        ).expanduser().resolve(
            strict=False
        )

        errors = []

        if not source.is_dir():
            errors.append(
                "Import source is not a readable directory."
            )

            return AssetPlan(
                source_root=source,
                moves=(),
                skipped=(),
                errors=tuple(errors),
            )

        if self._overlaps(
            source,
            overlays,
        ):
            errors.append(
                "Overlay destination overlaps the import source."
            )

        if self._overlaps(
            source,
            shaders,
        ):
            errors.append(
                "Shader destination overlaps the import source."
            )

        if errors:
            return AssetPlan(
                source_root=source,
                moves=(),
                skipped=(),
                errors=tuple(errors),
            )

        files = sorted(
            (
                path
                for path in source.rglob("*")
                if path.is_file()
            ),
            key=lambda path: (
                str(
                    path.relative_to(source)
                ).casefold()
            ),
        )

        planned = {}
        recognized = set()

        for path in files:
            if path.suffix.casefold() != ".cfg":
                continue

            references = self._overlay_references(
                path
            )

            if not references:
                continue

            self._add_move(
                planned,
                errors,
                "overlay",
                path,
                overlays
                / path.relative_to(source),
            )
            recognized.add(path)

            for reference in references:
                image = self._resolve_reference(
                    path,
                    reference,
                )

                try:
                    relative = image.relative_to(
                        source
                    )
                except ValueError:
                    errors.append(
                        "Overlay reference escapes "
                        f"the import source: {image}"
                    )
                    continue

                if (
                    image.suffix.casefold()
                    not in OVERLAY_IMAGE_EXTENSIONS
                ):
                    errors.append(
                        "Overlay reference is not a "
                        f"supported image: {image}"
                    )
                    continue

                if not image.is_file():
                    errors.append(
                        "Overlay image is missing: "
                        f"{image}"
                    )
                    continue

                self._add_move(
                    planned,
                    errors,
                    "overlay",
                    image,
                    overlays / relative,
                )
                recognized.add(image)

        for path in files:
            if (
                path.suffix.casefold()
                not in SHADER_EXTENSIONS
            ):
                continue

            self._add_move(
                planned,
                errors,
                "shader",
                path,
                shaders
                / path.relative_to(source),
            )
            recognized.add(path)

        moves = tuple(
            sorted(
                planned.values(),
                key=lambda move: (
                    move.category,
                    str(
                        move.destination
                    ).casefold(),
                ),
            )
        )

        skipped = tuple(
            path
            for path in files
            if path not in recognized
        )

        return AssetPlan(
            source_root=source,
            moves=moves,
            skipped=skipped,
            errors=tuple(
                dict.fromkeys(
                    errors
                )
            ),
        )

    def plan_shader_package(
        self,
        source_directory,
        shader_directory,
    ):
        source = Path(
            source_directory
        ).expanduser().resolve(
            strict=False
        )
        shader_root = Path(
            shader_directory
        ).expanduser().resolve(
            strict=False
        )
        destination = (
            shader_root
            / source.name
        )

        errors = []

        if not source.is_dir():
            errors.append(
                "Shader package source is not "
                "a readable directory."
            )

            return AssetPackagePlan(
                category="shader",
                source=source,
                destination=destination,
                file_count=0,
                total_bytes=0,
                errors=tuple(errors),
            )

        if self._overlaps(
            source,
            destination,
        ):
            errors.append(
                "Shader destination overlaps "
                "the package source."
            )

        if destination.exists():
            errors.append(
                "Shader package destination "
                f"already exists: {destination}"
            )

        symbolic_links = [
            path
            for path in source.rglob("*")
            if path.is_symlink()
        ]

        if symbolic_links:
            errors.append(
                "Shader package contains "
                "symbolic links."
            )

        files = sorted(
            (
                path
                for path in source.rglob("*")
                if path.is_file()
                and not path.is_symlink()
            ),
            key=lambda path: (
                str(
                    path.relative_to(source)
                ).casefold()
            ),
        )

        presets = [
            path
            for path in files
            if path.suffix.casefold()
            in {
                ".cgp",
                ".glslp",
                ".slangp",
            }
        ]

        if not presets:
            errors.append(
                "Directory contains no supported "
                "shader presets."
            )

        overlay_descriptors = [
            path
            for path in files
            if (
                path.suffix.casefold() == ".cfg"
                and self._overlay_references(path)
            )
        ]

        if overlay_descriptors:
            errors.append(
                "Directory also contains overlay "
                "descriptors and is not a pure "
                "shader package."
            )

        total_bytes = 0

        for file_path in files:
            try:
                total_bytes += (
                    file_path.stat().st_size
                )
            except OSError:
                errors.append(
                    "Shader package file cannot "
                    f"be read: {file_path}"
                )

        return AssetPackagePlan(
            category="shader",
            source=source,
            destination=destination,
            file_count=len(files),
            total_bytes=total_bytes,
            errors=tuple(
                dict.fromkeys(
                    errors
                )
            ),
        )

    def execute_package(
        self,
        plan,
    ):
        if not isinstance(
            plan,
            AssetPackagePlan,
        ):
            raise TypeError(
                "Expected an AssetPackagePlan."
            )

        if not plan.ready:
            raise ValueError(
                "Asset package plan is not ready."
            )

        if not plan.source.is_dir():
            raise ValueError(
                "Package source no longer exists."
            )

        if plan.destination.exists():
            raise ValueError(
                "Package destination now exists."
            )

        current_files = [
            path
            for path in plan.source.rglob("*")
            if path.is_file()
            and not path.is_symlink()
        ]

        if len(current_files) != plan.file_count:
            raise ValueError(
                "Package contents changed after "
                "planning."
            )

        current_bytes = sum(
            path.stat().st_size
            for path in current_files
        )

        if current_bytes != plan.total_bytes:
            raise ValueError(
                "Package contents changed after "
                "planning."
            )

        plan.destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            shutil.move(
                str(plan.source),
                str(plan.destination),
            )
        except Exception as exc:
            rollback_error = None

            if (
                plan.destination.exists()
                and not plan.source.exists()
            ):
                try:
                    shutil.move(
                        str(plan.destination),
                        str(plan.source),
                    )
                except Exception as rollback_exc:
                    rollback_error = (
                        rollback_exc
                    )

            if rollback_error is not None:
                raise RuntimeError(
                    "Shader package move and "
                    "rollback failed."
                ) from rollback_error

            raise RuntimeError(
                "Shader package move failed."
            ) from exc

        if (
            plan.source.exists()
            or not plan.destination.is_dir()
        ):
            try:
                if (
                    plan.destination.exists()
                    and not plan.source.exists()
                ):
                    shutil.move(
                        str(plan.destination),
                        str(plan.source),
                    )
            except Exception as rollback_exc:
                raise RuntimeError(
                    "Shader package verification "
                    "and rollback failed."
                ) from rollback_exc

            raise RuntimeError(
                "Shader package move could not "
                "be verified and was rolled back."
            )

        return AssetPackageResult(
            category=plan.category,
            source=plan.source,
            destination=plan.destination,
            file_count=plan.file_count,
            total_bytes=plan.total_bytes,
        )

    def execute(
        self,
        plan,
    ):
        if not isinstance(
            plan,
            AssetPlan,
        ):
            raise TypeError(
                "Expected an AssetPlan."
            )

        if not plan.ready:
            raise ValueError(
                "Asset plan is not ready."
            )

        self._validate_execution_plan(
            plan
        )

        completed = []
        created_directories = []

        try:
            for move in plan.moves:
                self._create_parent_directories(
                    move.destination.parent,
                    created_directories,
                )

                shutil.move(
                    str(move.source),
                    str(move.destination),
                )

                completed.append(move)
        except Exception as exc:
            rollback_errors = (
                self._rollback(
                    completed,
                    created_directories,
                )
            )

            message = (
                "Asset move failed; completed "
                "moves were rolled back."
            )

            if rollback_errors:
                message = (
                    "Asset move and rollback failed: "
                    + "; ".join(
                        rollback_errors
                    )
                )

            raise RuntimeError(
                message
            ) from exc

        return AssetExecutionResult(
            moved=tuple(completed)
        )

    @staticmethod
    def _validate_execution_plan(
        plan,
    ):
        destinations = set()

        for move in plan.moves:
            if not move.source.is_file():
                raise ValueError(
                    "Planned source no longer exists: "
                    f"{move.source}"
                )

            if move.destination in destinations:
                raise ValueError(
                    "Duplicate destination in plan: "
                    f"{move.destination}"
                )

            destinations.add(
                move.destination
            )

            if move.destination.exists():
                raise ValueError(
                    "Planned destination now exists: "
                    f"{move.destination}"
                )

    @staticmethod
    def _create_parent_directories(
        directory,
        created_directories,
    ):
        missing = []
        current = directory

        while not current.exists():
            missing.append(
                current
            )
            current = current.parent

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        for created in reversed(
            missing
        ):
            if created not in created_directories:
                created_directories.append(
                    created
                )

    @staticmethod
    def _rollback(
        completed,
        created_directories,
    ):
        errors = []

        for move in reversed(
            completed
        ):
            try:
                move.source.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                if move.destination.exists():
                    shutil.move(
                        str(move.destination),
                        str(move.source),
                    )
            except Exception as exc:
                errors.append(
                    f"{move.destination}: {exc}"
                )

        for directory in reversed(
            created_directories
        ):
            try:
                directory.rmdir()
            except OSError:
                pass

        return tuple(errors)

    @staticmethod
    def _overlaps(
        first,
        second,
    ):
        try:
            first.relative_to(second)
            return True
        except ValueError:
            pass

        try:
            second.relative_to(first)
            return True
        except ValueError:
            return False

    @staticmethod
    def _resolve_reference(
        config_path,
        reference,
    ):
        path = Path(
            reference
        ).expanduser()

        if not path.is_absolute():
            path = (
                config_path.parent
                / path
            )

        return path.resolve(
            strict=False
        )

    @staticmethod
    def _overlay_references(
        config_path,
    ):
        try:
            lines = config_path.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()
        except OSError:
            return ()

        references = []

        for line in lines:
            stripped = line.strip()

            if (
                not stripped
                or stripped.startswith("#")
                or "=" not in stripped
            ):
                continue

            key, value = stripped.split(
                "=",
                1,
            )

            key = key.strip().casefold()

            if not (
                key.startswith("overlay")
                and key.endswith("_overlay")
            ):
                continue

            value = (
                value.strip()
                .strip('"')
                .strip("'")
            )

            if (
                value
                and value not in references
            ):
                references.append(value)

        return tuple(references)

    @staticmethod
    def _add_move(
        planned,
        errors,
        category,
        source,
        destination,
    ):
        destination = destination.resolve(
            strict=False
        )

        existing = planned.get(
            destination
        )

        if (
            existing is not None
            and existing.source != source
        ):
            errors.append(
                "Multiple files target the same "
                f"destination: {destination}"
            )
            return

        if destination.exists():
            errors.append(
                "Destination already exists: "
                f"{destination}"
            )
            return

        planned[destination] = AssetMove(
            category=category,
            source=source,
            destination=destination,
        )
