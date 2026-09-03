import json
import os
from pathlib import Path


def _default_state_file() -> Path:
    xdg_config_home = os.environ.get(
        "XDG_CONFIG_HOME"
    )

    if xdg_config_home:
        config_home = Path(
            xdg_config_home
        ).expanduser()
    else:
        config_home = (
            Path.home()
            / ".config"
        )

    return (
        config_home
        / "retrovault"
        / "library-state.json"
    )


def game_identity(game) -> str:
    rom = getattr(
        game,
        "rom",
        "",
    )

    if not rom:
        raise ValueError(
            "Cannot persist Library state "
            "for a game without a ROM path."
        )

    return str(
        Path(rom)
        .expanduser()
        .resolve(strict=False)
    )


class LibraryState:
    def __init__(
        self,
        state_file=None,
    ):
        self.state_file = Path(
            state_file
            or _default_state_file()
        ).expanduser()

    def _read(self):
        if not self.state_file.is_file():
            return {
                "favorites": [],
            }

        try:
            data = json.loads(
                self.state_file.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid RetroVault Library "
                f"state: {self.state_file}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "RetroVault Library state "
                "must contain a JSON object."
            )

        favorites = data.get(
            "favorites",
            [],
        )

        if not isinstance(
            favorites,
            list,
        ):
            raise ValueError(
                "RetroVault Library favorites "
                "must contain a JSON list."
            )

        if not all(
            isinstance(item, str)
            for item in favorites
        ):
            raise ValueError(
                "RetroVault Library favorites "
                "must contain string identities."
            )

        return {
            "favorites": list(
                dict.fromkeys(
                    favorites
                )
            ),
        }

    def _write(self, data):
        self.state_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = (
            self.state_file.parent
            / (
                self.state_file.name
                + ".tmp"
            )
        )

        payload = json.dumps(
            data,
            indent=2,
            sort_keys=True,
        ) + "\n"

        try:
            with temporary.open(
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write(
                    payload
                )

                handle.flush()

                os.fsync(
                    handle.fileno()
                )

            os.replace(
                temporary,
                self.state_file,
            )
        finally:
            if temporary.exists():
                temporary.unlink()

    def favorites(self):
        return set(
            self._read()[
                "favorites"
            ]
        )

    def is_favorite(
        self,
        game,
    ):
        return (
            game_identity(game)
            in self.favorites()
        )

    def set_favorite(
        self,
        game,
        favorite,
    ):
        identity = game_identity(
            game
        )

        data = self._read()

        favorites = set(
            data["favorites"]
        )

        if favorite:
            favorites.add(
                identity
            )
        else:
            favorites.discard(
                identity
            )

        data["favorites"] = sorted(
            favorites
        )

        self._write(
            data
        )

    def apply(
        self,
        games,
    ):
        favorites = self.favorites()

        for game in games:
            rom = getattr(
                game,
                "rom",
                "",
            )

            if not rom:
                game.favorite = False
                continue

            game.favorite = (
                game_identity(game)
                in favorites
            )

        return games
