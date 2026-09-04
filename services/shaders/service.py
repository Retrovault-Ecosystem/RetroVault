from pathlib import Path

from .models import ShaderPreset


SUPPORTED_PRESET_EXTENSIONS = {
    ".cgp": "CG",
    ".glslp": "GLSL",
    ".slangp": "Slang",
}

SUPPORTED_SHADER_EXTENSIONS = {
    ".cg",
    ".glsl",
    ".slang",
}


class ShaderService:
    """Read installed RetroArch shader presets."""

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

        presets = sorted(
            (
                path
                for path in root.rglob("*")
                if (
                    path.is_file()
                    and path.suffix.casefold()
                    in SUPPORTED_PRESET_EXTENSIONS
                )
            ),
            key=lambda path: (
                str(
                    path.relative_to(root)
                ).casefold()
            ),
        )

        return [
            self._read_preset(
                preset
            )
            for preset in presets
        ]

    def _read_preset(
        self,
        preset_path,
    ):
        references = []

        try:
            lines = preset_path.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()
        except OSError:
            lines = []

        for line in lines:
            reference = self._shader_reference(
                line
            )

            if reference is None:
                continue

            shader_path = Path(
                reference
            ).expanduser()

            if not shader_path.is_absolute():
                shader_path = (
                    preset_path.parent
                    / shader_path
                )

            shader_path = shader_path.resolve(
                strict=False
            )

            if (
                shader_path.suffix.casefold()
                not in (
                    SUPPORTED_SHADER_EXTENSIONS
                    | set(
                        SUPPORTED_PRESET_EXTENSIONS
                    )
                )
            ):
                continue

            if shader_path not in references:
                references.append(
                    shader_path
                )

        shaders = tuple(references)

        missing = tuple(
            shader
            for shader in shaders
            if not shader.is_file()
        )

        relative = preset_path.relative_to(
            self.directory
        )

        name = (
            preset_path.stem
            .replace("_", " ")
            .replace("-", " ")
            .strip()
        )

        preset_type = (
            SUPPORTED_PRESET_EXTENSIONS[
                preset_path.suffix.casefold()
            ]
        )

        return ShaderPreset(
            name=name or preset_path.stem,
            preset_path=preset_path,
            relative_preset=relative,
            preset_type=preset_type,
            shader_paths=shaders,
            missing_shaders=missing,
        )

    @staticmethod
    def _shader_reference(
        line,
    ):
        stripped = line.strip()

        if not stripped:
            return None

        if stripped.casefold().startswith(
            "#reference"
        ):
            value = stripped[
                len("#reference"):
            ].strip()

            value = (
                value.strip('"')
                .strip("'")
            )

            return value or None

        if (
            stripped.startswith("#")
            or "=" not in stripped
        ):
            return None

        key, value = stripped.split(
            "=",
            1,
        )

        key = key.strip().casefold()

        if not (
            key.startswith("shader")
            and key[6:].isdigit()
        ):
            return None

        value = (
            value.strip()
            .strip('"')
            .strip("'")
        )

        return value or None
