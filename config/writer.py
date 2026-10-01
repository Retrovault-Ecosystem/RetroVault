import json
import os
import tempfile
from .loader import _merge_config
from .validation import validate_config
from pathlib import Path

from .loader import (
    _default_runtime_file,
)




class ConfigWriter:
    def __init__(
        self,
        runtime_file=None,
    ):
        self.runtime_file = Path(
            runtime_file
            or _default_runtime_file()
        ).expanduser()

    def _validate_mapping(
        self,
        data,
    ):
        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "RetroVault runtime configuration "
                "must be a mapping."
            )

    def _read_existing(self):
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

        self._validate_mapping(
            data
        )

        return data

    def write(
        self,
        data,
    ):
        self._validate_mapping(
            data
        )

        validate_config(data)

        self.runtime_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
        fd, name = tempfile.mkstemp(prefix=self.runtime_file.name + '.', suffix='.tmp',
                                    dir=self.runtime_file.parent)
        os.close(fd)
        temporary = Path(name)

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
                self.runtime_file,
            )
        finally:
            if temporary.exists():
                temporary.unlink()

    def update(
        self,
        overrides,
    ):
        self._validate_mapping(
            overrides
        )

        existing = (
            self._read_existing()
        )

        merged = _merge_config(
            existing,
            overrides,
        )

        self.write(
            merged
        )
