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


def test_assign_default_shader_preserves_other_fields(
    tmp_path,
):
    path = (
        tmp_path
        / "presentation-state.json"
    )

    store = PresentationStore(path)

    store.save(
        default=PresentationProfile(
            shader="/old/default.slangp",
            overlay="/default/overlay.cfg",
            artwork="/default/art.png",
        ),
        systems={
            "platform.nintendo.nes": (
                PresentationProfile(
                    shader="/old/nes.slangp",
                    overlay="/nes/overlay.cfg",
                )
            )
        },
        games={
            "/roms/game.nes": (
                PresentationProfile(
                    shader="/old/game.slangp",
                    artwork="/game/art.png",
                )
            )
        },
    )

    store.assign_default_shader(
        "/new/default.slangp"
    )

    data = store.load()

    assert data["default"] == PresentationProfile(
        shader="/new/default.slangp",
        overlay="/default/overlay.cfg",
        artwork="/default/art.png",
    )

    assert data["systems"][
        "platform.nintendo.nes"
    ] == PresentationProfile(
        shader="/old/nes.slangp",
        overlay="/nes/overlay.cfg",
    )

    assert data["games"][
        "/roms/game.nes"
    ] == PresentationProfile(
        shader="/old/game.slangp",
        artwork="/game/art.png",
    )


def test_assign_system_shader_preserves_profile_and_other_scopes(
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
                    shader="/old/nes.slangp",
                    overlay="/nes/overlay.cfg",
                    artwork="/nes/art.png",
                )
            ),
            "platform.nintendo.snes": (
                PresentationProfile(
                    shader="/snes.slangp",
                )
            ),
        },
        games={
            "/roms/game.nes": (
                PresentationProfile(
                    shader="/game.slangp",
                )
            )
        },
    )

    store.assign_system_shader(
        "platform.nintendo.nes",
        "/new/nes.slangp",
    )

    data = store.load()

    assert data["systems"][
        "platform.nintendo.nes"
    ] == PresentationProfile(
        shader="/new/nes.slangp",
        overlay="/nes/overlay.cfg",
        artwork="/nes/art.png",
    )

    assert data["systems"][
        "platform.nintendo.snes"
    ].shader == "/snes.slangp"

    assert data["default"].shader == (
        "/default.slangp"
    )

    assert data["games"][
        "/roms/game.nes"
    ].shader == "/game.slangp"


def test_assign_game_shader_preserves_profile_and_other_scopes(
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
                    shader="/nes.slangp",
                )
            )
        },
        games={
            "/roms/game.nes": (
                PresentationProfile(
                    shader="/old/game.slangp",
                    overlay="/game/overlay.cfg",
                    artwork="/game/art.png",
                )
            ),
        },
    )

    store.assign_game_shader(
        "/roms/game.nes",
        "/new/game.slangp",
    )

    data = store.load()

    assert data["games"][
        "/roms/game.nes"
    ] == PresentationProfile(
        shader="/new/game.slangp",
        overlay="/game/overlay.cfg",
        artwork="/game/art.png",
    )

    assert data["default"].shader == (
        "/default.slangp"
    )

    assert data["systems"][
        "platform.nintendo.nes"
    ].shader == "/nes.slangp"


def test_assignment_methods_reject_invalid_identity(
    tmp_path,
):
    path = (
        tmp_path
        / "presentation-state.json"
    )

    store = PresentationStore(path)

    import pytest

    with pytest.raises(ValueError):
        store.assign_system_shader(
            "",
            "/shader.slangp",
        )

    with pytest.raises(ValueError):
        store.assign_game_shader(
            "",
            "/shader.slangp",
        )

    assert not path.exists()


def test_assign_default_overlay_preserves_other_fields(
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
            overlay="/old/default.cfg",
            artwork="/default.png",
        ),
        systems={
            "platform.nintendo.nes": (
                PresentationProfile(
                    shader="/nes.slangp",
                    overlay="/nes.cfg",
                )
            )
        },
        games={
            "/roms/game.nes": (
                PresentationProfile(
                    overlay="/game.cfg",
                    artwork="/game.png",
                )
            )
        },
    )

    store.assign_default_overlay(
        "/new/default.cfg"
    )

    data = store.load()

    assert data["default"] == (
        PresentationProfile(
            shader="/default.slangp",
            overlay="/new/default.cfg",
            artwork="/default.png",
        )
    )

    assert data["systems"][
        "platform.nintendo.nes"
    ] == PresentationProfile(
        shader="/nes.slangp",
        overlay="/nes.cfg",
    )

    assert data["games"][
        "/roms/game.nes"
    ] == PresentationProfile(
        overlay="/game.cfg",
        artwork="/game.png",
    )


def test_assign_system_overlay_preserves_profile_and_other_scopes(
    tmp_path,
):
    path = (
        tmp_path
        / "presentation-state.json"
    )

    store = PresentationStore(path)

    store.save(
        default=PresentationProfile(
            overlay="/default.cfg",
        ),
        systems={
            "platform.nintendo.nes": (
                PresentationProfile(
                    shader="/nes.slangp",
                    overlay="/old/nes.cfg",
                    artwork="/nes.png",
                )
            ),
            "platform.nintendo.snes": (
                PresentationProfile(
                    overlay="/snes.cfg",
                )
            ),
        },
        games={
            "/roms/game.nes": (
                PresentationProfile(
                    overlay="/game.cfg",
                )
            )
        },
    )

    store.assign_system_overlay(
        "platform.nintendo.nes",
        "/new/nes.cfg",
    )

    data = store.load()

    assert data["systems"][
        "platform.nintendo.nes"
    ] == PresentationProfile(
        shader="/nes.slangp",
        overlay="/new/nes.cfg",
        artwork="/nes.png",
    )

    assert data["systems"][
        "platform.nintendo.snes"
    ].overlay == "/snes.cfg"

    assert data["default"].overlay == (
        "/default.cfg"
    )

    assert data["games"][
        "/roms/game.nes"
    ].overlay == "/game.cfg"


def test_assign_game_overlay_preserves_profile_and_other_scopes(
    tmp_path,
):
    path = (
        tmp_path
        / "presentation-state.json"
    )

    store = PresentationStore(path)

    store.save(
        default=PresentationProfile(
            overlay="/default.cfg",
        ),
        systems={
            "platform.nintendo.nes": (
                PresentationProfile(
                    overlay="/nes.cfg",
                )
            )
        },
        games={
            "/roms/game.nes": (
                PresentationProfile(
                    shader="/game.slangp",
                    overlay="/old/game.cfg",
                    artwork="/game.png",
                )
            ),
            "/roms/other.nes": (
                PresentationProfile(
                    overlay="/other.cfg",
                )
            ),
        },
    )

    store.assign_game_overlay(
        "/roms/game.nes",
        "/new/game.cfg",
    )

    data = store.load()

    assert data["games"][
        "/roms/game.nes"
    ] == PresentationProfile(
        shader="/game.slangp",
        overlay="/new/game.cfg",
        artwork="/game.png",
    )

    assert data["games"][
        "/roms/other.nes"
    ].overlay == "/other.cfg"

    assert data["systems"][
        "platform.nintendo.nes"
    ].overlay == "/nes.cfg"

    assert data["default"].overlay == (
        "/default.cfg"
    )


def test_overlay_assignment_validates_values(
    tmp_path,
):
    store = PresentationStore(
        tmp_path
        / "presentation-state.json"
    )

    with pytest.raises(
        ValueError,
        match="Presentation overlay must be a string",
    ):
        store.assign_default_overlay(
            None
        )

    with pytest.raises(
        ValueError,
        match="Presentation system identity",
    ):
        store.assign_system_overlay(
            "",
            "/nes.cfg",
        )

    with pytest.raises(
        ValueError,
        match="Presentation overlay must be a string",
    ):
        store.assign_system_overlay(
            "platform.nintendo.nes",
            None,
        )

    with pytest.raises(
        ValueError,
        match="Presentation game identity",
    ):
        store.assign_game_overlay(
            "",
            "/game.cfg",
        )

    with pytest.raises(
        ValueError,
        match="Presentation overlay must be a string",
    ):
        store.assign_game_overlay(
            "/roms/game.nes",
            None,
        )
