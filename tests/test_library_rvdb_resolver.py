import json

import pytest

from services.library.rvdb_resolver import (
    RVDBLibraryResolver,
)


@pytest.fixture
def resolver(tmp_path):
    bundle = {
        "nodes": {
            "platform.alpha": {
                "id": "platform.alpha",
                "type": "platform",
                "name": "Alpha System",
                "aliases": [
                    "Alpha",
                    "AS",
                ],
                "extensions": [
                    "abc",
                ],
            },
            "platform.beta": {
                "id": "platform.beta",
                "type": "platform",
                "name": "Beta System",
                "aliases": [],
                "extensions": [
                    "shared",
                ],
            },
            "platform.gamma": {
                "id": "platform.gamma",
                "type": "platform",
                "name": "Gamma System",
                "aliases": [],
                "extensions": [
                    "shared",
                ],
            },
            "core.alpha": {
                "id": "core.alpha",
                "type": "core",
                "name": "Alpha Core",
            },
            "core.one": {
                "id": "core.one",
                "type": "core",
                "name": "Core One",
            },
            "core.two": {
                "id": "core.two",
                "type": "core",
                "name": "Core Two",
            },
        },
        "edges": {
            "platform.alpha": {
                "supports_core": [
                    "core.alpha",
                ],
            },
            "platform.beta": {
                "supports_core": [
                    "core.one",
                    "core.two",
                ],
            },
            "platform.gamma": {},
            "core.alpha": {},
            "core.one": {},
            "core.two": {},
        },
    }

    path = tmp_path / "rvdb.bundle.json"

    path.write_text(
        json.dumps(bundle),
        encoding="utf-8",
    )

    return RVDBLibraryResolver.from_bundle(
        path
    )


def test_unique_extension_resolves_platform(
    resolver,
):
    platform = (
        resolver.platform_for_extension(
            ".ABC"
        )
    )

    assert platform is not None

    assert platform.id == (
        "platform.alpha"
    )


def test_ambiguous_extension_refuses_guess(
    resolver,
):
    matches = (
        resolver.platforms_for_extension(
            "shared"
        )
    )

    assert {
        platform.id
        for platform in matches
    } == {
        "platform.beta",
        "platform.gamma",
    }

    assert (
        resolver.platform_for_extension(
            "shared"
        )
        is None
    )


def test_unknown_extension_returns_none(
    resolver,
):
    assert (
        resolver.platform_for_extension(
            ".missing"
        )
        is None
    )


def test_canonical_name_resolves_platform(
    resolver,
):
    platform = (
        resolver.platform_for_name(
            "Alpha System"
        )
    )

    assert platform is not None

    assert platform.id == (
        "platform.alpha"
    )


def test_alias_resolves_platform_case_insensitively(
    resolver,
):
    platform = (
        resolver.platform_for_name(
            "  aLpHa  "
        )
    )

    assert platform is not None

    assert platform.id == (
        "platform.alpha"
    )


def test_supported_cores_come_from_rvdb(
    resolver,
):
    cores = resolver.supported_cores(
        "platform.alpha"
    )

    assert [
        core.id
        for core in cores
    ] == [
        "core.alpha",
    ]


def test_single_supported_core_is_preferred(
    resolver,
):
    core = resolver.preferred_core(
        "platform.alpha"
    )

    assert core is not None

    assert core.id == (
        "core.alpha"
    )


def test_multiple_supported_cores_refuse_policy_guess(
    resolver,
):
    assert (
        resolver.preferred_core(
            "platform.beta"
        )
        is None
    )


def test_no_supported_core_returns_none(
    resolver,
):
    assert (
        resolver.preferred_core(
            "platform.gamma"
        )
        is None
    )


def test_real_rvdb_unique_nes_extension():
    resolver = (
        RVDBLibraryResolver.from_bundle(
            "data/rvdb/rvdb.bundle.json"
        )
    )

    platform = (
        resolver.platform_for_extension(
            ".nes"
        )
    )

    assert platform is not None

    assert platform.id == (
        "platform.nintendo.nes"
    )

    assert platform.name == (
        "Nintendo Entertainment System"
    )


def test_real_rvdb_snes_alias():
    resolver = (
        RVDBLibraryResolver.from_bundle(
            "data/rvdb/rvdb.bundle.json"
        )
    )

    platform = (
        resolver.platform_for_name(
            "SNES"
        )
    )

    assert platform is not None

    assert platform.id == (
        "platform.nintendo.snes"
    )


def test_real_rvdb_chd_is_ambiguous():
    resolver = (
        RVDBLibraryResolver.from_bundle(
            "data/rvdb/rvdb.bundle.json"
        )
    )

    matches = (
        resolver.platforms_for_extension(
            ".chd"
        )
    )

    assert {
        platform.id
        for platform in matches
    } == {
        "platform.sega.dreamcast",
        "platform.sega.saturn",
    }

    assert (
        resolver.platform_for_extension(
            ".chd"
        )
        is None
    )


def test_real_rvdb_snes_does_not_choose_between_cores():
    resolver = (
        RVDBLibraryResolver.from_bundle(
            "data/rvdb/rvdb.bundle.json"
        )
    )

    cores = resolver.supported_cores(
        "platform.nintendo.snes"
    )

    assert {
        core.name
        for core in cores
    } == {
        "bsnes",
        "Snes9x",
    }

    assert (
        resolver.preferred_core(
            "platform.nintendo.snes"
        )
        is None
    )
