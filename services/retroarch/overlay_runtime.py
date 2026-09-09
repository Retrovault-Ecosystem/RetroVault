import atexit
import os
import tempfile
from pathlib import Path


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
        / "overlay-runtime"
    )


class OverlayRuntimeConfig:
    """
    Create transient RetroArch append-config files for overlays.

    The generated files belong to RetroVault's runtime session. They
    are intentionally not written into RetroArch's permanent config
    hierarchy.

    An overlay may opt into additional RetroArch runtime geometry
    through a sibling ``<overlay-stem>.runtime.cfg`` descriptor.
    Only explicitly supported runtime keys are accepted.
    """

    RUNTIME_KEYS = (
        "aspect_ratio_index",
        "video_force_aspect",
        "custom_viewport_x",
        "custom_viewport_y",
        "custom_viewport_width",
        "custom_viewport_height",
    )

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
    def _config_value(
        value,
    ):
        return (
            str(value)
            .replace("\\", "\\\\")
            .replace('"', '\\"')
        )

    @classmethod
    def _runtime_descriptor_payload(
        cls,
        overlay_path,
    ):
        runtime_path = (
            overlay_path
            .with_suffix(".runtime.cfg")
        )

        if not runtime_path.exists():
            return ""

        if not runtime_path.is_file():
            raise ValueError(
                "Overlay runtime descriptor "
                "must be a regular file: "
                f"{runtime_path}"
            )

        values = {}

        for raw_line in runtime_path.read_text(
            encoding="utf-8"
        ).splitlines():
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            key, separator, value = (
                line.partition("=")
            )

            if not separator:
                raise ValueError(
                    "Invalid overlay runtime "
                    "descriptor line: "
                    f"{raw_line}"
                )

            key = key.strip()
            value = value.strip()

            if key not in cls.RUNTIME_KEYS:
                raise ValueError(
                    "Unsupported overlay runtime "
                    f"setting: {key}"
                )

            if key in values:
                raise ValueError(
                    "Duplicate overlay runtime "
                    f"setting: {key}"
                )

            if (
                len(value) < 2
                or value[0] != '"'
                or value[-1] != '"'
            ):
                raise ValueError(
                    "Overlay runtime values must be quoted."
                )

            values[key] = value

        return "".join(
            f"{key} = {values[key]}\n"
            for key in cls.RUNTIME_KEYS
            if key in values
        )

    def create(
        self,
        overlay,
    ):
        if not isinstance(overlay, str):
            raise ValueError(
                "Overlay path must be a string."
            )

        if not overlay:
            raise ValueError(
                "Overlay path cannot be empty."
            )

        overlay_path = (
            Path(overlay)
            .expanduser()
            .resolve(strict=False)
        )

        if not overlay_path.is_file():
            raise ValueError(
                "Overlay configuration does not exist: "
                f"{overlay_path}"
            )

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        escaped = self._config_value(
            overlay_path
        )

        runtime_payload = (
            self._runtime_descriptor_payload(
                overlay_path
            )
        )

        payload = (
            f'input_overlay = "{escaped}"\n'
            'input_overlay_enable = "true"\n'
            + runtime_payload
        )

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="overlay-",
            suffix=".cfg",
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
