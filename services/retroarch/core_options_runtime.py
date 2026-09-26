import atexit
import os
import tempfile
from pathlib import Path

from services.presentation.platform_policy import (
    PlatformPresentationPolicyRegistry,
)
from services.retroarch.core_identity import (
    canonical_libretro_core_identity,
)


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

    POLICIES is retained only as a backward-compatible read-only-style
    snapshot for callers/tests that inspect the historical public
    attribute. Canonical policy ownership remains exclusively in
    PlatformPresentationPolicyRegistry.
    """

    POLICIES = {
        core_identity: dict(
            policy.core_options
        )
        for policy in (
            PlatformPresentationPolicyRegistry.all()
        )
        for core_identity in policy.core_identities
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
        # Preserve the historical CoreOptionsRuntimeConfig validation
        # contract while delegating all actual identity normalization to
        # the shared Libretro representation boundary.
        if not isinstance(core, str):
            raise ValueError(
                "Core path must be a string."
            )

        if not core:
            raise ValueError(
                "Core path cannot be empty."
            )

        return canonical_libretro_core_identity(
            core
        )

    @classmethod
    def policy_for(
        cls,
        core,
        platform_id=None,
    ):
        identity = cls._core_identity(
            core
        )

        policy = (
            PlatformPresentationPolicyRegistry.resolve(
                platform_id=platform_id,
                core_identity=identity,
            )
        )

        if policy is None:
            return {}

        return dict(
            policy.core_options
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
        platform_id=None,
    ):
        policy = self.policy_for(
            core,
            platform_id=platform_id,
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
