import shutil
from pathlib import Path

from .models import (
    AssetExecutionResult,
    AssetMove,
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
