from pathlib import Path

import pytest

from services.library.bulk_import import (
    BulkImporter,
)
from services.library.models import Game


def test_bulk_import_recursively_discovers_supported_roms(
    tmp_path,
):
    nested = (
        tmp_path
        / "Nintendo"
        / "NES"
    )

    nested.mkdir(
        parents=True
    )

    rom = nested / "Mario.nes"

    rom.write_bytes(
        b"rom"
    )

    result = BulkImporter().import_directory(
        tmp_path
    )

    assert result.discovered_count == 1
    assert result.duplicate_count == 0
    assert len(result.games) == 1

    assert Path(
        result.games[0].rom
    ) == rom


def test_bulk_import_ignores_unsupported_files(
    tmp_path,
):
    (tmp_path / "notes.txt").write_text(
        "not a rom",
        encoding="utf-8",
    )

    result = BulkImporter().import_directory(
        tmp_path
    )

    assert result.discovered_count == 0
    assert result.games == ()


def test_bulk_import_rejects_missing_directory(
    tmp_path,
):
    missing = (
        tmp_path
        / "missing"
    )

    with pytest.raises(
        ValueError,
        match="Source path does not exist",
    ):
        BulkImporter().import_directory(
            missing
        )


def test_bulk_import_rejects_file_source(
    tmp_path,
):
    source = tmp_path / "roms"

    source.write_text(
        "not a directory",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Source is not a directory",
    ):
        BulkImporter().import_directory(
            source
        )


def test_bulk_import_preserves_rvdb_resolver():
    resolver = object()

    importer = BulkImporter(
        rvdb_resolver=resolver
    )

    assert (
        importer.scanner.rvdb_resolver
        is resolver
    )


class DuplicateScanner:
    def scan(
        self,
        source,
    ):
        rom = str(
            Path(source.path)
            / "Mario.nes"
        )

        game = Game(
            name="Mario",
            platform=(
                "Nintendo Entertainment System"
            ),
            year=0,
            genre="",
            core="fceumm",
            rom=rom,
            source=source.name,
        )

        duplicate = Game(
            name="Mario Duplicate",
            platform=(
                "Nintendo Entertainment System"
            ),
            year=0,
            genre="",
            core="fceumm",
            rom=rom,
            source=source.name,
        )

        return [
            game,
            duplicate,
        ]


def test_bulk_import_deduplicates_by_rom_identity(
    tmp_path,
):
    importer = BulkImporter(
        scanner=DuplicateScanner()
    )

    result = importer.import_directory(
        tmp_path
    )

    assert result.discovered_count == 1
    assert result.duplicate_count == 1
    assert len(result.games) == 1
    assert result.games[0].name == "Mario"


class ReverseScanner:
    def scan(
        self,
        source,
    ):
        root = Path(
            source.path
        )

        return [
            Game(
                name="Zelda",
                platform=(
                    "Nintendo Entertainment System"
                ),
                year=0,
                genre="",
                core="fceumm",
                rom=str(root / "Zelda.nes"),
                source=source.name,
            ),
            Game(
                name="Mario",
                platform=(
                    "Nintendo Entertainment System"
                ),
                year=0,
                genre="",
                core="fceumm",
                rom=str(root / "Mario.nes"),
                source=source.name,
            ),
        ]


def test_bulk_import_result_is_deterministic(
    tmp_path,
):
    importer = BulkImporter(
        scanner=ReverseScanner()
    )

    result = importer.import_directory(
        tmp_path
    )

    assert [
        game.name
        for game in result.games
    ] == [
        "Mario",
        "Zelda",
    ]


def test_bulk_import_result_records_source_metadata(
    tmp_path,
):
    result = BulkImporter().import_directory(
        tmp_path,
        source_id="starter-suite",
        source_name="Starter Suite",
    )

    assert result.source.id == (
        "starter-suite"
    )

    assert result.source.name == (
        "Starter Suite"
    )

    assert result.source.enabled is True
    assert result.source.type == "local"

    assert result.source.path == str(
        tmp_path.resolve()
    )


def test_bulk_import_does_not_create_runtime_state(
    tmp_path,
    monkeypatch,
):
    config_home = (
        tmp_path
        / "config"
    )

    monkeypatch.setenv(
        "XDG_CONFIG_HOME",
        str(config_home),
    )

    rom_root = (
        tmp_path
        / "roms"
    )

    rom_root.mkdir()

    (rom_root / "Mario.nes").write_bytes(
        b"rom"
    )

    BulkImporter().import_directory(
        rom_root
    )

    assert not (
        config_home
        / "retrovault"
        / "runtime.json"
    ).exists()

    assert not (
        config_home
        / "retrovault"
        / "library-state.json"
    ).exists()
