import json

import pytest

from services.presentation import (
    PresentationProfile,
    PresentationResolver,
    PresentationStore,
)


def test_absent_file_returns_empty_typed_state(
    tmp_path,
):
    path = (
        tmp_path
        / "presentation-state.json"
    )

    store = PresentationStore(path)

    data = store.load()

    assert data == {
        "version": 1,
        "default": PresentationProfile(),
        "systems": {},
        "games": {},
    }

    assert not path.exists()


def test_save_round_trips_typed_assignments(
    tmp_path,
):
    path = (
        tmp_path
        / "presentation-state.json"
    )

    store = PresentationStore(path)

    default = PresentationProfile(
        artwork="/presentation/default.png",
    )

    systems = {
        "platform.nintendo.nes": (
            PresentationProfile(
                shader="/presentation/nes.slangp",
            )
        ),
    }

    games = {
        "/roms/Duck Tales 2 (U).nes": (
            PresentationProfile(
                overlay="/presentation/duck.cfg",
            )
        ),
    }

    store.save(
        default=default,
        systems=systems,
        games=games,
    )

    assert store.load() == {
        "version": 1,
        "default": default,
        "systems": systems,
        "games": games,
    }


def test_save_uses_versioned_json_document(
    tmp_path,
):
    path = (
        tmp_path
        / "presentation-state.json"
    )

    store = PresentationStore(path)

    store.save(
        default=PresentationProfile(
            shader="/default.slangp",
        ),
        systems={
            "platform.nintendo.nes": (
                PresentationProfile(
                    overlay="/nes.cfg",
                )
            ),
        },
        games={},
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert data == {
        "version": 1,
        "default": {
            "shader": "/default.slangp",
            "overlay": "",
            "artwork": "",
        },
        "systems": {
            "platform.nintendo.nes": {
                "shader": "",
                "overlay": "/nes.cfg",
                "artwork": "",
            },
        },
        "games": {},
    }


def test_save_is_atomic_and_removes_temporary_file(
    tmp_path,
):
    path = (
        tmp_path
        / "presentation-state.json"
    )

    temporary = (
        tmp_path
        / "presentation-state.json.tmp"
    )

    store = PresentationStore(path)

    store.save(
        default=PresentationProfile(
            shader="/first.slangp",
        )
    )

    store.save(
        default=PresentationProfile(
            shader="/second.slangp",
        )
    )

    assert path.is_file()
    assert not temporary.exists()

    assert (
        store.load()["default"]
        == PresentationProfile(
            shader="/second.slangp",
        )
    )


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {
            "version": 2,
            "default": {},
            "systems": {},
            "games": {},
        },
        {
            "version": 1,
            "default": [],
            "systems": {},
            "games": {},
        },
        {
            "version": 1,
            "default": {},
            "systems": [],
            "games": {},
        },
        {
            "version": 1,
            "default": {},
            "systems": {},
            "games": [],
        },
        {
            "version": 1,
            "default": {
                "shader": 123,
            },
            "systems": {},
            "games": {},
        },
        {
            "version": 1,
            "default": {},
            "systems": {
                "platform.nintendo.nes": {
                    "unknown": "value",
                },
            },
            "games": {},
        },
        {
            "version": 1,
            "default": {},
            "systems": {},
            "games": {},
            "unexpected": {},
        },
    ],
)
def test_invalid_documents_are_rejected(
    tmp_path,
    payload,
):
    path = (
        tmp_path
        / "presentation-state.json"
    )

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        PresentationStore(path).load()


def test_invalid_json_is_rejected(
    tmp_path,
):
    path = (
        tmp_path
        / "presentation-state.json"
    )

    path.write_text(
        "{broken",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Invalid RetroVault presentation state",
    ):
        PresentationStore(path).load()


def test_save_rejects_untyped_profiles(
    tmp_path,
):
    store = PresentationStore(
        tmp_path
        / "presentation-state.json"
    )

    with pytest.raises(ValueError):
        store.save(
            systems={
                "platform.nintendo.nes": {
                    "shader": "/nes.slangp",
                }
            }
        )


def test_resolver_rehydrates_persisted_precedence(
    tmp_path,
):
    path = (
        tmp_path
        / "presentation-state.json"
    )

    store = PresentationStore(path)

    store.save(
        default=PresentationProfile(
            artwork="/default.png",
        ),
        systems={
            "platform.nintendo.nes": (
                PresentationProfile(
                    shader="/nes.slangp",
                )
            ),
        },
        games={
            "/roms/Duck Tales 2 (U).nes": (
                PresentationProfile(
                    overlay="/duck.cfg",
                )
            ),
        },
    )

    resolver = store.resolver()

    assert isinstance(
        resolver,
        PresentationResolver,
    )

    assert resolver.default == (
        PresentationProfile(
            artwork="/default.png",
        )
    )

    assert resolver.systems == {
        "platform.nintendo.nes": (
            PresentationProfile(
                shader="/nes.slangp",
            )
        )
    }

    assert resolver.games == {
        "/roms/Duck Tales 2 (U).nes": (
            PresentationProfile(
                overlay="/duck.cfg",
            )
        )
    }


def test_default_path_honors_xdg_config_home(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(
        "XDG_CONFIG_HOME",
        str(tmp_path),
    )

    store = PresentationStore()

    assert store.presentation_file == (
        tmp_path
        / "retrovault"
        / "presentation-state.json"
    )
