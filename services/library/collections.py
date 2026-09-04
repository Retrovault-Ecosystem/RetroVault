import json
import os
from pathlib import Path

from services.library.state import game_identity



def _default_collections_file() -> Path:
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
        / "collections.json"
    )


def _normalized_name(name) -> str:
    if not isinstance(name, str):
        raise ValueError(
            "Collection name must be a string."
        )

    normalized = name.strip()

    if not normalized:
        raise ValueError(
            "Collection name cannot be empty."
        )

    return normalized


class CollectionStore:
    def __init__(
        self,
        collections_file=None,
    ):
        self.collections_file = Path(
            collections_file
            or _default_collections_file()
        ).expanduser()

    def _empty_data(self):
        return {
            "version": 1,
            "collections": [],
        }

    def _read(self):
        if not self.collections_file.is_file():
            return self._empty_data()

        try:
            data = json.loads(
                self.collections_file.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid RetroVault collections file: "
                f"{self.collections_file}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "RetroVault collections must contain "
                "a JSON object."
            )

        if data.get("version") != 1:
            raise ValueError(
                "Unsupported RetroVault collections version."
            )

        collections = data.get(
            "collections"
        )

        if not isinstance(collections, list):
            raise ValueError(
                "RetroVault collections must contain "
                "a JSON list."
            )

        seen_names = set()
        normalized_collections = []

        for collection in collections:
            if not isinstance(collection, dict):
                raise ValueError(
                    "Each collection must be a JSON object."
                )

            name = _normalized_name(
                collection.get("name")
            )

            name_key = name.casefold()

            if name_key in seen_names:
                raise ValueError(
                    "Collection names must be unique."
                )

            seen_names.add(name_key)

            games = collection.get(
                "games",
                [],
            )

            if not isinstance(games, list):
                raise ValueError(
                    "Collection games must contain "
                    "a JSON list."
                )

            if not all(
                isinstance(identity, str)
                for identity in games
            ):
                raise ValueError(
                    "Collection games must contain "
                    "string identities."
                )

            normalized_collections.append(
                {
                    "name": name,
                    "games": list(
                        dict.fromkeys(games)
                    ),
                }
            )

        return {
            "version": 1,
            "collections": normalized_collections,
        }

    def _write(self, data):
        self.collections_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = (
            self.collections_file.parent
            / (
                self.collections_file.name
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
                handle.write(payload)
                handle.flush()
                os.fsync(
                    handle.fileno()
                )

            os.replace(
                temporary,
                self.collections_file,
            )
        finally:
            if temporary.exists():
                temporary.unlink()

    def _find(self, data, name):
        normalized = _normalized_name(name)
        name_key = normalized.casefold()

        for collection in data["collections"]:
            if collection["name"].casefold() == name_key:
                return collection

        raise KeyError(
            f"Unknown collection: {normalized}"
        )

    def names(self):
        return [
            collection["name"]
            for collection in self._read()[
                "collections"
            ]
        ]

    def create(self, name):
        normalized = _normalized_name(name)
        data = self._read()

        if any(
            collection["name"].casefold()
            == normalized.casefold()
            for collection in data["collections"]
        ):
            raise ValueError(
                f"Collection already exists: {normalized}"
            )

        data["collections"].append(
            {
                "name": normalized,
                "games": [],
            }
        )

        self._write(data)

        return normalized

    def rename(self, current_name, new_name):
        normalized = _normalized_name(new_name)
        data = self._read()
        collection = self._find(
            data,
            current_name,
        )

        if any(
            candidate is not collection
            and candidate["name"].casefold()
            == normalized.casefold()
            for candidate in data["collections"]
        ):
            raise ValueError(
                f"Collection already exists: {normalized}"
            )

        collection["name"] = normalized
        self._write(data)

        return normalized

    def delete(self, name):
        data = self._read()
        collection = self._find(
            data,
            name,
        )

        data["collections"].remove(
            collection
        )

        self._write(data)

    def identities(self, name):
        data = self._read()

        return list(
            self._find(
                data,
                name,
            )["games"]
        )

    def add_game(self, name, game):
        identity = game_identity(game)
        data = self._read()
        collection = self._find(
            data,
            name,
        )

        if identity not in collection["games"]:
            collection["games"].append(
                identity
            )
            self._write(data)

        return identity

    def remove_game(self, name, game):
        identity = game_identity(game)
        data = self._read()
        collection = self._find(
            data,
            name,
        )

        if identity in collection["games"]:
            collection["games"].remove(
                identity
            )
            self._write(data)

        return identity
