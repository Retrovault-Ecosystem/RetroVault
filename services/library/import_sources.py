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
