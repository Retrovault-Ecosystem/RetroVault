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
        / "session-runtime"
    )


class RetroArchSessionConfig:
    """
    Create RetroVault-owned transient session configuration.

    RetroVault presentation must begin from a deterministic state.

    The session baseline explicitly clears presentation state that may
    otherwise leak from RetroArch's global/core/content configuration
    into a RetroVault-controlled launch.

    Permanent RetroArch configuration is never modified.

    Platform presentation is layered after this baseline by the normal
    RetroVault overlay/shader runtime services.
    """

    BASELINE = (
        'input_overlay_enable = "false"\n'
        'input_overlay = ""\n'
        'video_shader_enable = "false"\n'
        'video_shader = ""\n'
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

    def create(
        self,
        core_options_path=None,
    ):
        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = self.BASELINE

        if core_options_path:
            path = (
                Path(core_options_path)
                .expanduser()
                .resolve(strict=False)
            )

            escaped = (
                str(path)
                .replace("\\\\", "\\\\\\\\")
                .replace('"', '\\\"')
            )

            payload += (
                f'core_options_path = "{escaped}"\n'
                'global_core_options = "true"\n'
            )

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="session-",
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

    def cleanup(self):
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
