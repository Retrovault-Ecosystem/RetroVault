from pathlib import Path

from config import ConfigLoader, ConfigWriter


def _canonical_path(path):
    return str(
        Path(path)
        .expanduser()
        .resolve()
    )


class ImportSourceStore:

    def __init__(
        self,
        config_loader=None,
        config_writer=None,
    ):
        self.loader = (
            config_loader
            if config_loader is not None
            else ConfigLoader()
        )

        self.writer = (
            config_writer
            if config_writer is not None
            else ConfigWriter()
        )

    def sources(self):
        config = self.loader.load()

        return list(
            config
            .get("library", {})
            .get("sources", [])
        )

    def persist_directory(
        self,
        directory,
        *,
        source_id="bulk-import",
        source_name="Bulk Import",
    ):
        canonical = _canonical_path(
            directory
        )

        sources = self.sources()

        for source in sources:
            try:
                existing = _canonical_path(
                    source.get("path", "")
                )
            except (OSError, RuntimeError):
                existing = str(
                    source.get("path", "")
                )

            if existing == canonical:
                return {
                    "added": False,
                    "source": source,
                    "sources": tuple(sources),
                }

        existing_ids = {
            str(
                source.get("id", "")
            )
            for source in sources
        }

        candidate = str(source_id)
        suffix = 2

        while candidate in existing_ids:
            candidate = (
                f"{source_id}-{suffix}"
            )
            suffix += 1

        source = {
            "id": candidate,
            "name": str(source_name),
            "enabled": True,
            "type": "local",
            "path": canonical,
        }

        sources.append(
            source
        )

        self.writer.update(
            {
                "library": {
                    "sources": sources,
                }
            }
        )

        return {
            "added": True,
            "source": source,
            "sources": tuple(sources),
        }


    def rename_source(
        self,
        source_id,
        name,
    ):
        source_id = str(
            source_id
        )
        name = str(
            name
        ).strip()

        if not name:
            raise ValueError(
                "Library source name is required."
            )

        sources = self.sources()

        for index, source in enumerate(
            sources
        ):
            if str(
                source.get(
                    "id",
                    "",
                )
            ) != source_id:
                continue

            updated = dict(
                source
            )
            updated[
                "name"
            ] = name

            sources[
                index
            ] = updated

            self.writer.update(
                {
                    "library": {
                        "sources": sources,
                    }
                }
            )

            return {
                "source": updated,
                "sources": tuple(
                    sources
                ),
            }

        raise ValueError(
            "Library source not found: "
            f"{source_id}"
        )


    def set_source_enabled(
        self,
        source_id,
        enabled,
    ):
        source_id = str(
            source_id
        )
        enabled = bool(
            enabled
        )

        sources = self.sources()

        target_index = None

        for index, source in enumerate(
            sources
        ):
            if str(
                source.get(
                    "id",
                    "",
                )
            ) == source_id:
                target_index = index
                break

        if target_index is None:
            raise ValueError(
                "Library source not found: "
                f"{source_id}"
            )

        if not enabled:
            enabled_count = sum(
                1
                for source in sources
                if source.get(
                    "enabled",
                    False,
                )
            )

            if (
                sources[
                    target_index
                ].get(
                    "enabled",
                    False,
                )
                and enabled_count <= 1
            ):
                raise ValueError(
                    "At least one library source "
                    "must remain enabled."
                )

        updated = dict(
            sources[
                target_index
            ]
        )
        updated[
            "enabled"
        ] = enabled

        sources[
            target_index
        ] = updated

        self.writer.update(
            {
                "library": {
                    "sources": sources,
                }
            }
        )

        return {
            "source": updated,
            "sources": tuple(
                sources
            ),
        }


    def remove_source(
        self,
        source_id,
    ):
        source_id = str(
            source_id
        )

        sources = self.sources()

        target_index = None

        for index, source in enumerate(
            sources
        ):
            if str(
                source.get(
                    "id",
                    "",
                )
            ) == source_id:
                target_index = index
                break

        if target_index is None:
            raise ValueError(
                "Library source not found: "
                f"{source_id}"
            )

        source = sources[
            target_index
        ]

        if (
            source.get(
                "enabled",
                False,
            )
            and sum(
                1
                for candidate in sources
                if candidate.get(
                    "enabled",
                    False,
                )
            ) <= 1
        ):
            raise ValueError(
                "At least one library source "
                "must remain enabled."
            )

        removed = sources.pop(
            target_index
        )

        self.writer.update(
            {
                "library": {
                    "sources": sources,
                }
            }
        )

        return {
            "removed": removed,
            "sources": tuple(
                sources
            ),
        }
