from __future__ import annotations

from pathlib import Path
import re
import shutil
import tempfile


class CheatRuntimeConfig:
    """
    Build an isolated one-launch RetroArch cheat database.

    RetroArch game-specific cheat autoload resolves:

        cheat_database_path
            / <core library_name>
            / <game cheat filename>

    The generated append config therefore points RetroArch at a
    temporary database root and enables apply-after-load.

    RetroArch's persistent configuration is never modified.
    """

    INFO_ROOTS = (
        Path(
            "/var/lib/flatpak/app/"
            "org.libretro.RetroArch/current/active/"
            "files/share/libretro/info"
        ),
        (
            Path.home()
            / ".var/app/org.libretro.RetroArch/"
            "config/retroarch/info"
        ),
    )

    def __init__(
        self,
        runtime_root=None,
        info_roots=None,
    ):
        if runtime_root is None:
            runtime_root = (
                Path.home()
                / ".cache"
                / "retrovault"
                / "cheat-runtime"
            )

        self.runtime_root = Path(
            runtime_root
        ).expanduser()

        self.info_roots = tuple(
            Path(root).expanduser()
            for root in (
                info_roots
                if info_roots is not None
                else self.INFO_ROOTS
            )
        )

    @staticmethod
    def _quote(value: str) -> str:
        return (
            str(value)
            .replace("\\", "\\\\")
            .replace('"', '\\"')
        )

    @staticmethod
    def _core_stem(core) -> str:
        name = Path(
            str(core)
        ).name

        if name.endswith(
            "_libretro.so"
        ):
            return name[
                :-len("_libretro.so")
            ]

        if name.endswith(
            "_libretro.dylib"
        ):
            return name[
                :-len("_libretro.dylib")
            ]

        if name.endswith(
            "_libretro.dll"
        ):
            return name[
                :-len("_libretro.dll")
            ]

        return Path(name).stem

    @staticmethod
    def _info_value(
        path: Path,
        key: str,
    ) -> str:
        try:
            text = path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            return ""

        match = re.search(
            rf'(?m)^{re.escape(key)}\s*=\s*"([^"]*)"',
            text,
        )

        if not match:
            return ""

        return match.group(1).strip()

    def core_library_name(
        self,
        core,
    ) -> str:
        """
        Resolve RetroArch's libretro library_name from the matching
        core .info metadata.

        The .info 'corename' field is the installed metadata contract
        corresponding to the core's library_name.

        We intentionally do not substitute RetroVault platform names.
        """

        stem = self._core_stem(
            core
        )

        info_name = (
            stem
            + "_libretro.info"
        )

        for root in self.info_roots:
            path = root / info_name

            if not path.is_file():
                continue

            value = self._info_value(
                path,
                "corename",
            )

            if value:
                return value

        raise ValueError(
            "Unable to determine RetroArch core library name "
            f"for {Path(str(core)).name}."
        )

    @staticmethod
    def game_cheat_filename(
        runtime_rom,
    ) -> str:
        """
        RetroArch's runloop game-specific cheat filename follows the
        loaded content basename with a .cht suffix.
        """

        name = Path(
            str(runtime_rom)
        ).name

        if not name:
            raise ValueError(
                "Runtime ROM filename is required "
                "for cheat autoload."
            )

        return (
            Path(name).stem
            + ".cht"
        )

    def create(
        self,
        cheat_file,
        core,
        runtime_rom,
    ) -> str:
        cheat_path = Path(
            str(cheat_file)
        ).expanduser()

        if (
            not cheat_path.is_file()
            or cheat_path.suffix.casefold()
            != ".cht"
        ):
            raise ValueError(
                "RetroVault cheat runtime requires "
                "an existing .cht file."
            )

        library_name = (
            self.core_library_name(
                core
            )
        )

        cheat_filename = (
            self.game_cheat_filename(
                runtime_rom
            )
        )

        self.runtime_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        launch_root = Path(
            tempfile.mkdtemp(
                prefix="retrovault-cheats-",
                dir=self.runtime_root,
            )
        )

        database_root = (
            launch_root
            / "database"
        )

        core_root = (
            database_root
            / library_name
        )

        core_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        runtime_cheat = (
            core_root
            / cheat_filename
        )

        shutil.copyfile(
            cheat_path,
            runtime_cheat,
        )

        config_path = (
            launch_root
            / "retroarch-cheats.cfg"
        )

        try:
            config_path.write_text(
                (
                    'cheat_database_path = "'
                    + self._quote(
                        str(
                            database_root.resolve()
                        )
                    )
                    + '"\n'
                    + 'apply_cheats_after_load = "true"\n'
                ),
                encoding="utf-8",
            )
        except Exception:
            shutil.rmtree(
                launch_root,
                ignore_errors=True,
            )
            raise

        return str(
            config_path
        )
