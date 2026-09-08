from __future__ import annotations

import json
from dataclasses import dataclass

from services.library.rvdb_resolver import (
    RVDBLibraryResolver,
)
from services.library.scanner import (
    RomScanner,
)
from services.rvdb import (
    RVDBGameSummary,
    RVDBService,
)


NES = "platform.nintendo.nes"
SNES = "platform.nintendo.snes"


@dataclass
class Source:
    name: str
    path: str


def write_bundle(
    path,
    *,
    ambiguous=False,
):
    nodes = {
        NES: {
            "id": NES,
            "type": "platform",
            "name": "Nintendo Entertainment System",
            "aliases": ["NES"],
            "extensions": ["nes"],
        },
        SNES: {
            "id": SNES,
            "type": "platform",
            "name": "Super Nintendo",
            "aliases": ["SNES"],
            "extensions": ["sfc"],
        },
        "game.duck_tales_2": {
            "id": "game.duck_tales_2",
            "type": "game",
            "name": "Duck Tales 2",
            "aliases": [
                "DuckTales 2",
            ],
        },
        "game.super_metroid": {
            "id": "game.super_metroid",
            "type": "game",
            "name": "Super Metroid",
            "aliases": [
                "Super Metroid (SNES)",
            ],
        },
    }

    edges = {
        NES: {},
        SNES: {},
        "game.duck_tales_2": {
            "platform": [
                NES,
            ],
        },
        "game.super_metroid": {
            "platform": [
                SNES,
            ],
        },
    }

    if ambiguous:
        nodes[
            "game.duck_tales_2_alt"
        ] = {
            "id": "game.duck_tales_2_alt",
            "type": "game",
            "name": "Duck Tales 2",
            "aliases": [],
        }

        edges[
            "game.duck_tales_2_alt"
        ] = {
            "platform": [
                NES,
            ],
        }

    path.write_text(
        json.dumps(
            {
                "nodes": nodes,
                "edges": edges,
            }
        ),
        encoding="utf-8",
    )


def make_resolver(
    tmp_path,
    *,
    ambiguous=False,
):
    bundle = (
        tmp_path
        / "rvdb.bundle.json"
    )

    write_bundle(
        bundle,
        ambiguous=ambiguous,
    )

    return RVDBLibraryResolver.from_bundle(
        bundle
    )


def test_package_exports_game_summary():
    assert RVDBGameSummary.__name__ == (
        "RVDBGameSummary"
    )


def test_service_exposes_typed_game_summaries(
    tmp_path,
):
    bundle = (
        tmp_path
        / "rvdb.bundle.json"
    )

    write_bundle(
        bundle
    )

    games = RVDBService.from_bundle(
        bundle
    ).games()

    assert games == (
        RVDBGameSummary(
            id="game.duck_tales_2",
            name="Duck Tales 2",
            aliases=(
                "DuckTales 2",
            ),
            platforms=(
                NES,
            ),
        ),
        RVDBGameSummary(
            id="game.super_metroid",
            name="Super Metroid",
            aliases=(
                "Super Metroid (SNES)",
            ),
            platforms=(
                SNES,
            ),
        ),
    )


def test_resolver_matches_title_and_platform(
    tmp_path,
):
    resolver = make_resolver(
        tmp_path
    )

    game = resolver.game_for_name(
        "Duck Tales 2",
        NES,
    )

    assert game is not None
    assert game.id == (
        "game.duck_tales_2"
    )


def test_resolver_matches_alias_case_insensitively(
    tmp_path,
):
    resolver = make_resolver(
        tmp_path
    )

    game = resolver.game_for_name(
        "ducktales 2",
        NES,
    )

    assert game is not None
    assert game.id == (
        "game.duck_tales_2"
    )


def test_resolver_requires_matching_platform(
    tmp_path,
):
    resolver = make_resolver(
        tmp_path
    )

    assert resolver.game_for_name(
        "Duck Tales 2",
        SNES,
    ) is None


def test_resolver_requires_platform_identity(
    tmp_path,
):
    resolver = make_resolver(
        tmp_path
    )

    assert resolver.game_for_name(
        "Duck Tales 2",
        "",
    ) is None


def test_resolver_rejects_ambiguous_title_platform(
    tmp_path,
):
    resolver = make_resolver(
        tmp_path,
        ambiguous=True,
    )

    assert resolver.game_for_name(
        "Duck Tales 2",
        NES,
    ) is None


def test_scanner_enriches_canonical_game_id(
    tmp_path,
):
    resolver = make_resolver(
        tmp_path
    )

    root = (
        tmp_path
        / "roms"
    )

    root.mkdir()

    (
        root
        / "Duck Tales 2.nes"
    ).write_bytes(
        b"test"
    )

    game = RomScanner(
        rvdb_resolver=resolver,
    ).scan(
        Source(
            name="Test Library",
            path=str(root),
        )
    )[0]

    assert game.rvdb_platform_id == NES
    assert game.rvdb_game_id == (
        "game.duck_tales_2"
    )


def test_scanner_leaves_game_id_empty_without_match(
    tmp_path,
):
    resolver = make_resolver(
        tmp_path
    )

    root = (
        tmp_path
        / "roms"
    )

    root.mkdir()

    (
        root
        / "Unknown Game.nes"
    ).write_bytes(
        b"test"
    )

    game = RomScanner(
        rvdb_resolver=resolver,
    ).scan(
        Source(
            name="Test Library",
            path=str(root),
        )
    )[0]

    assert game.rvdb_platform_id == NES
    assert game.rvdb_game_id == ""


def test_scanner_without_rvdb_keeps_ids_empty(
    tmp_path,
):
    root = (
        tmp_path
        / "roms"
    )

    root.mkdir()

    (
        root
        / "Duck Tales 2.nes"
    ).write_bytes(
        b"test"
    )

    game = RomScanner().scan(
        Source(
            name="Test Library",
            path=str(root),
        )
    )[0]

    assert game.rvdb_platform_id == ""
    assert game.rvdb_game_id == ""
