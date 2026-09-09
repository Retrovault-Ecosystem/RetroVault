import atexit
import os
import tempfile
from pathlib import Path
from typing import Mapping


def _default_runtime_directory() -> Path:
    cache_home = os.environ.get(
        "XDG_CACHE_HOME"
    )

    if cache_home:
        root = Path(
            cache_home
        ).expanduser()
    else:
        root = (
            Path.home()
            / ".cache"
        )

    return (
        root
        / "retrovault"
        / "shader-runtime"
    )


class ShaderRuntimeConfig:
    """
    Create transient shader presets around an effective shader.

    The selected shader remains authoritative. When no runtime
    parameters are supplied, it is returned unchanged.

    When parameters are supplied, RetroVault creates a temporary
    preset which references the effective shader and contains only
    the requested parameter overrides.

    The service is intentionally presentation-agnostic. It contains
    no RVV-, platform-, shader-pack-, or parameter-specific policy.
    """

    def __init__(
        self,
        directory=None,
    ):
        self.directory = Path(
            directory
            if directory is not None
            else _default_runtime_directory()
        ).expanduser()

        self._created = []

        atexit.register(
            self.cleanup
        )

    @staticmethod
    def _preset_value(
        value,
    ):
        return (
            str(value)
            .replace("\\", "\\\\")
            .replace('"', '\\"')
        )

    @staticmethod
    def _validate_parameter_name(
        name,
    ):
        if not isinstance(name, str):
            raise ValueError(
                "Shader runtime parameter "
                "name must be a string."
            )

        if not name:
            raise ValueError(
                "Shader runtime parameter "
                "name cannot be empty."
            )

        if not (
            name[0].isalpha()
            or name[0] == "_"
        ):
            raise ValueError(
                "Invalid shader runtime "
                f"parameter name: {name}"
            )

        if not all(
            character.isalnum()
            or character == "_"
            for character in name
        ):
            raise ValueError(
                "Invalid shader runtime "
                f"parameter name: {name}"
            )

    @staticmethod
    def parameters_for_overlay(
        overlay,
    ):
        if not overlay:
            return {}

        if not isinstance(overlay, str):
            raise ValueError(
                "Overlay path must be a string."
            )

        overlay_path = (
            Path(overlay)
            .expanduser()
            .resolve(strict=False)
        )

        descriptor = (
            overlay_path
            .with_suffix(".shader.cfg")
        )

        if not descriptor.exists():
            return {}

        if not descriptor.is_file():
            raise ValueError(
                "Shader runtime descriptor "
                "must be a regular file: "
                f"{descriptor}"
            )

        parameters = {}

        for raw_line in descriptor.read_text(
            encoding="utf-8"
        ).splitlines():
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            name, separator, value = (
                line.partition("=")
            )

            if not separator:
                raise ValueError(
                    "Invalid shader runtime "
                    "descriptor line: "
                    f"{raw_line}"
                )

            name = name.strip()
            value = value.strip()

            ShaderRuntimeConfig._validate_parameter_name(
                name
            )

            if name in parameters:
                raise ValueError(
                    "Duplicate shader runtime "
                    f"parameter: {name}"
                )

            if (
                len(value) < 2
                or value[0] != '"'
                or value[-1] != '"'
            ):
                raise ValueError(
                    "Shader runtime parameter "
                    "values must be quoted."
                )

            parameters[name] = value[1:-1]

        return parameters

    def resolve(
        self,
        shader,
        parameters=None,
    ):
        if not isinstance(shader, str):
            raise ValueError(
                "Shader path must be a string."
            )

        if not shader:
            return ""

        shader_path = (
            Path(shader)
            .expanduser()
            .resolve(strict=False)
        )

        if not shader_path.is_file():
            raise ValueError(
                "Shader preset does not exist: "
                f"{shader_path}"
            )

        if parameters is None:
            parameters = {}

        if not isinstance(
            parameters,
            Mapping,
        ):
            raise ValueError(
                "Shader runtime parameters "
                "must be a mapping."
            )

        if not parameters:
            return str(shader_path)

        normalized = []

        for name, value in parameters.items():
            self._validate_parameter_name(
                name
            )

            if value is None:
                raise ValueError(
                    "Shader runtime parameter "
                    f"value cannot be null: {name}"
                )

            normalized.append(
                (
                    name,
                    self._preset_value(
                        value
                    ),
                )
            )

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        reference = self._preset_value(
            shader_path
        )

        payload = (
            f'#reference "{reference}"\n'
            "\n"
            + "".join(
                f'{name} = "{value}"\n'
                for name, value in normalized
            )
        )

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="shader-",
            suffix=".slangp",
            dir=self.directory,
            delete=False,
        ) as handle:
            handle.write(
                payload
            )
            handle.flush()
            os.fsync(
                handle.fileno()
            )

            runtime_file = Path(
                handle.name
            )

        self._created.append(
            runtime_file
        )

        return str(runtime_file)

    def cleanup(
        self,
    ):
        remaining = []

        for path in self._created:
            try:
                path.unlink(
                    missing_ok=True
                )
            except OSError:
                remaining.append(
                    path
                )

        self._created = remaining
