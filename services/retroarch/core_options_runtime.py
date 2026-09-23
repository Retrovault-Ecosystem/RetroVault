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
        / "core-options-runtime"
    )


class CoreOptionsRuntimeConfig:
    """
    Create transient RetroArch core-option files owned by RetroVault.

    Core options that affect the core-reported visible area must not
    depend on persistent state from an external RetroArch installation.

    Policies are selected by core identity, never by individual game.

    The default safety policy for an explicitly managed core is to
    preserve legitimate core-provided pixels on every edge unless a
    future platform contract deliberately specifies otherwise.

    Permanent RetroArch configuration is never modified.
    """

    POLICIES = {
        "fceumm": {
            "fceumm_overscan_h_left": "0",
            "fceumm_overscan_h_right": "0",
            "fceumm_overscan_v_top": "0",
            "fceumm_overscan_v_bottom": "0",
        },
    }

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
    def _core_identity(
        core,
    ):
        if not isinstance(core, str):
            raise ValueError(
                "Core path must be a string."
            )

        if not core:
            raise ValueError(
                "Core path cannot be empty."
            )

        name = (
            Path(core)
            .name
            .lower()
        )

        if name.endswith(
            "_libretro.so"
        ):
            name = name[
                :-len("_libretro.so")
            ]
        elif name.endswith(
            "_libretro.dll"
        ):
            name = name[
                :-len("_libretro.dll")
            ]
        elif name.endswith(
            "_libretro.dylib"
        ):
            name = name[
                :-len("_libretro.dylib")
            ]
        elif name.endswith(
            "_libretro"
        ):
            name = name[
                :-len("_libretro")
            ]

        if name.startswith(
            "lr-"
        ):
            name = name[3:]

        return name

    @classmethod
    def policy_for(
        cls,
        core,
    ):
        identity = cls._core_identity(
            core
        )

        policy = cls.POLICIES.get(
            identity
        )

        if policy is None:
            return {}

        return dict(
            policy
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
        core,
    ):
        policy = self.policy_for(
            core
        )

        if not policy:
            return None

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="core-options-",
            suffix=".cfg",
            dir=self.directory,
            delete=False,
        ) as handle:
            for key, value in policy.items():
                escaped = self._config_value(
                    value
                )

                handle.write(
                    f'{key} = "{escaped}"\n'
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

        return str(
            runtime_file
        )

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
