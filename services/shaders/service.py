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

            normalized = (
                reference
                .replace("\\\\", "/")
            )

            if self._contains_runtime_token(
                normalized
            ):
                # RetroArch substitutes these tokens
                # when the preset is loaded. They are
                # dynamic references, not missing files.
                continue

            reference_path = Path(
                normalized
            ).expanduser()

            if (
                reference_path.suffix.casefold()
                not in (
                    SUPPORTED_SHADER_EXTENSIONS
                    | set(
                        SUPPORTED_PRESET_EXTENSIONS
                    )
                )
            ):
                continue

            shader_path = self._resolve_reference(
                preset_path,
                normalized,
            )

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
    def _contains_runtime_token(
        reference,
    ):
        """Return True for RetroArch runtime wildcards."""
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

    def _resolve_reference(
        self,
        preset_path,
        reference,
    ):
        """
        Resolve a static RetroArch shader reference.

        Supports:
        - ordinary preset-relative references
        - :/shaders/... shader-root references
        - canonical root-relative shader directories
        - portable remapping of absolute RetroArch
          shader paths from another installation
        - unique case-insensitive filesystem matches
        """
        normalized = reference.replace(
            "\\",
            "/",
        )

        root = self.directory.resolve(
            strict=False
        )

        root_relative = (
            self._shader_root_relative(
                normalized
            )
        )

        if root_relative is not None:
            candidate = (
                root / root_relative
            )
        else:
            candidate_path = Path(
                normalized
            ).expanduser()

            if candidate_path.is_absolute():
                candidate = candidate_path
            else:
                candidate = (
                    preset_path.parent
                    / candidate_path
                )

        candidate = candidate.resolve(
            strict=False
        )

        if candidate.is_file():
            return candidate

        casefold_candidate = (
            self._casefold_candidate(
                candidate
            )
        )

        if casefold_candidate.is_file():
            return casefold_candidate

        structural_candidate = (
            self._structural_fallback(
                preset_path,
                normalized,
                candidate,
            )
        )

        if (
            structural_candidate is not None
            and structural_candidate.is_file()
        ):
            return structural_candidate

        return candidate

    def _structural_fallback(
        self,
        preset_path,
        reference,
        candidate,
    ):
        """
        Resolve only audited package-layout mismatches.

        This is deliberately not a global filename search.

        Supported compatibility cases:

        1. Mega Bezel Variations presets whose legacy
           ../../../Base_CRT_Presets reference escapes
           the current Mega_Bezel/Presets directory.

        2. Mega Bezel crt-super-xbr whose preset uses
           shaders/<file> while the package stores the
           referenced shader directly beside the preset.
        """
        root = self.directory.resolve(
            strict=False
        )

        preset = preset_path.resolve(
            strict=False
        )

        normalized = reference.replace(
            "\\\\",
            "/",
        )

        try:
            preset_relative = preset.relative_to(
                root
            )
        except ValueError:
            return None

        parts = preset_relative.parts

        mega_variations_prefix = (
            "shaders_slang",
            "bezel",
            "Mega_Bezel",
            "Presets",
            "Variations",
        )

        if (
            len(parts) == 6
            and tuple(parts[:5])
            == mega_variations_prefix
            and normalized.startswith(
                "../../../Base_CRT_Presets/"
            )
        ):
            filename = normalized[
                len(
                    "../../../Base_CRT_Presets/"
                ):
            ]

            if (
                filename
                and "/" not in filename
                and "\\\\" not in filename
            ):
                fallback = (
                    root
                    / "shaders_slang"
                    / "bezel"
                    / "Mega_Bezel"
                    / "Presets"
                    / "Base_CRT_Presets"
                    / filename
                ).resolve(
                    strict=False
                )

                if fallback.is_file():
                    return fallback

        crt_super_xbr = (
            root
            / "shaders_slang"
            / "bezel"
            / "Mega_Bezel"
            / "shaders"
            / "hyllian"
            / "crt-super-xbr"
        ).resolve(
            strict=False
        )

        if (
            preset.parent == crt_super_xbr
            and preset.name
            == "crt-super-xbr.slangp"
            and normalized.startswith(
                "shaders/"
            )
        ):
            filename = normalized[
                len("shaders/"):
            ]

            if (
                filename
                and "/" not in filename
                and "\\\\" not in filename
            ):
                fallback = (
                    crt_super_xbr
                    / filename
                ).resolve(
                    strict=False
                )

                if fallback.is_file():
                    return fallback

        return None

    @staticmethod
    def _shader_root_relative(
        reference,
    ):
        normalized = reference.lstrip()

        pseudo_root = ":/shaders/"

        if normalized.startswith(
            pseudo_root
        ):
            return Path(
                normalized[
                    len(pseudo_root):
                ]
            )

        canonical_roots = (
            "shaders_slang/",
            "Mega_Bezel_Packs/",
            "blurs/",
            "reshade/",
        )

        if normalized.startswith(
            canonical_roots
        ):
            return Path(normalized)

        marker = "/retroarch/shaders/"

        lowered = normalized.casefold()
        marker_index = lowered.find(
            marker
        )

        if marker_index >= 0:
            relative = normalized[
                marker_index + len(marker):
            ]

            if relative:
                return Path(relative)

        return None

    def _casefold_candidate(
        self,
        candidate,
    ):
        """
        Resolve Linux case mismatches only when every
        differing path component has one unique match.

        Ambiguous case-insensitive matches remain missing.
        """
        root = self.directory.resolve(
            strict=False
        )

        try:
            relative = candidate.relative_to(
                root
            )
        except ValueError:
            return candidate

        current = root

        for part in relative.parts:
            exact = current / part

            if exact.exists():
                current = exact
                continue

            try:
                matches = [
                    child
                    for child in current.iterdir()
                    if (
                        child.name.casefold()
                        == part.casefold()
                    )
                ]
            except OSError:
                return candidate

            if len(matches) != 1:
                return candidate

            current = matches[0]

        return current.resolve(
            strict=False
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
