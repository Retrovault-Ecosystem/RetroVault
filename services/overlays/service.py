from pathlib import Path

from .models import Overlay


SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpeg",
    ".jpg",
    ".png",
    ".webp",
}


class OverlayService:
    """Read installed RetroArch overlay descriptors."""

    def __init__(
        self,
        directory,
    ):
        self.directory = Path(
            directory
        ).expanduser()

    def scan(self):
        root = self.directory

        if not root.is_dir():
            return []

        configs = sorted(
            (
                path
                for path in root.rglob("*")
                if (
                    path.is_file()
                    and path.suffix.casefold()
                    == ".cfg"
                )
            ),
            key=lambda path: (
                str(
                    path.relative_to(root)
                ).casefold()
            ),
        )

        return [
            self._read_overlay(
                config
            )
            for config in configs
        ]

    def _read_overlay(
        self,
        config_path,
    ):
        references = []

        try:
            lines = config_path.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()
        except OSError:
            lines = []

        for line in lines:
            reference = (
                self._image_reference(
                    line
                )
            )

            if reference is None:
                continue

            image_path = Path(
                reference
            ).expanduser()

            if not image_path.is_absolute():
                image_path = (
                    config_path.parent
                    / image_path
                )

            image_path = image_path.resolve(
                strict=False
            )

            if (
                image_path.suffix.casefold()
                not in SUPPORTED_IMAGE_EXTENSIONS
            ):
                continue

            if image_path not in references:
                references.append(
                    image_path
                )

        images = tuple(references)

        missing = tuple(
            image
            for image in images
            if not image.is_file()
        )

        relative = config_path.relative_to(
            self.directory
        )

        name = (
            config_path.stem
            .replace("_", " ")
            .replace("-", " ")
            .strip()
        )

        return Overlay(
            name=name or config_path.stem,
            config_path=config_path,
            relative_config=relative,
            image_paths=images,
            missing_images=missing,
        )

    @staticmethod
    def _image_reference(
        line,
    ):
        stripped = line.strip()

        if (
            not stripped
            or stripped.startswith("#")
            or "=" not in stripped
        ):
            return None

        key, value = stripped.split(
            "=",
            1,
        )

        key = key.strip().casefold()

        if not (
            key.startswith("overlay")
            and key.endswith("_overlay")
        ):
            return None

        value = (
            value.strip()
            .strip('"')
            .strip("'")
        )

        return value or None
