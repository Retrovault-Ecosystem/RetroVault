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
    def _config_value(
        value,
    ):
        return (
            str(value)
            .replace("\\", "\\\\")
            .replace('"', '\\"')
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

        payload = (
            f'input_overlay = "{escaped}"\n'
            'input_overlay_enable = "true"\n'
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
