import copy
import json
import os
from pathlib import Path

import yaml


DEFAULT_CONFIG_FILE = (
    Path(__file__).resolve().parent
    / "retroarch.yaml"
)


def _default_runtime_file() -> Path:
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
        / "runtime.json"
    )


def _merge_config(
    base,
    override,
):
    if not (
        isinstance(base, dict)
        and isinstance(
            override,
            dict,
        )
    ):
        return copy.deepcopy(
            override
        )

    result = copy.deepcopy(
        base
    )

    for key, value in (
        override.items()
    ):
        if (
            key in result
            and isinstance(
                result[key],
                dict,
            )
            and isinstance(
                value,
                dict,
            )
        ):
            result[key] = (
                _merge_config(
                    result[key],
                    value,
                )
            )
        else:
            result[key] = (
                copy.deepcopy(
                    value
                )
            )

    return result


class ConfigLoader:
    def __init__(
        self,
        default_file=None,
        runtime_file=None,
    ):
        self.default_file = Path(
            default_file
            or DEFAULT_CONFIG_FILE
        )

        self.runtime_file = Path(
            runtime_file
            or _default_runtime_file()
        ).expanduser()

    def _load_defaults(self):
        with self.default_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = yaml.safe_load(
                file
            )

        if data is None:
            return {}

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "RetroVault default configuration "
                "must contain a YAML mapping."
            )

        return data

    def _load_runtime_override(self):
        if not self.runtime_file.is_file():
            return {}

        try:
            data = json.loads(
                self.runtime_file.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid RetroVault runtime "
                f"configuration: {self.runtime_file}"
            ) from exc

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "RetroVault runtime configuration "
                "must contain a JSON object."
            )

        return data

    def load(self):
        defaults = (
            self._load_defaults()
        )

        runtime = (
            self._load_runtime_override()
        )

        return _merge_config(
            defaults,
            runtime,
        )
