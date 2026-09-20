from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

from PyQt6.QtWidgets import QApplication

from models.launch_profile import LaunchProfile
from services.cheats import (
    CheatCategory,
    CheatCode,
    CheatCodeType,
    CheatCollection,
    CheatIdentity,
    CheatService,
)
from services.library.models import Game
from services.retroarch.cheat_runtime import (
    CheatRuntimeConfig,
)
from ui.library.widgets.cheat_studio import (
    CheatStudio,
)


_APP = None


def app():
    global _APP

    existing = QApplication.instance()

    if existing is not None:
        _APP = existing
        return existing

    if _APP is None:
        _APP = QApplication([])

    return _APP


def game():
    return Game(
        name="Example Game (USA) (Rev A)",
        platform="NES",
        year=1987,
        genre="Platform",
        rom="/games/Example Game (USA) (Rev A).nes",
        core="lr-fceumm",
        canonical_title="Example Game",
        variant_category="revision",
        variant_region="USA",
        variant_language="English",
        variant_revision="Rev A",
    )


def collection():
    identity = CheatService.identity_for(
        game()
    )

    return CheatCollection(
        identity=identity,
        cheats=[
            CheatCode(
                name="Unlimited Lives",
                code="AAAA-BBBB",
                code_type=CheatCodeType.GAME_GENIE,
                category=CheatCategory.LIVES_HEALTH,
                source="Fixture",
            ),
            CheatCode(
                name="Level Select",
                code="CCCC-DDDD",
                code_type=CheatCodeType.GAME_GENIE,
                category=CheatCategory.LEVEL_STAGE,
                source="Fixture",
            ),
            CheatCode(
                name="Wrong Revision Code",
                code="EEEE-FFFF",
                code_type=CheatCodeType.GAME_GENIE,
                category=CheatCategory.GAMEPLAY,
                source="Fixture",
                compatible=False,
                compatibility_note="Different ROM revision.",
            ),
        ],
    )


class FakeService:
    def __init__(self):
        self.value = collection()

    def discover(
        self,
        game,
        archive_member="",
    ):
        return CheatCollection(
            identity=replace(
                self.value.identity,
                archive_member=archive_member,
            ),
            cheats=list(
                self.value.cheats
            ),
        )

    def manual_cheat(
        self,
        **kwargs,
    ):
        return CheatService.manual_cheat(
            **kwargs
        )

    def enable_all_compatible(
        self,
        cheats,
    ):
        return CheatService.enable_all_compatible(
            cheats
        )

    def disable_all(
        self,
        cheats,
    ):
        return CheatService.disable_all(
            cheats
        )


def test_studio_uses_exact_physical_edition():
    app()

    studio = CheatStudio(
        game(),
        archive_member="Example Game (USA) (Rev A).nes",
        cheat_service=FakeService(),
    )

    assert (
        studio.collection.identity.region
        == "USA"
    )
    assert (
        studio.collection.identity.language
        == "English"
    )
    assert (
        studio.collection.identity.revision
        == "Rev A"
    )
    assert (
        studio.collection.identity.archive_member
        == "Example Game (USA) (Rev A).nes"
    )


def test_enable_all_never_enables_incompatible():
    app()

    studio = CheatStudio(
        game(),
        cheat_service=FakeService(),
    )

    studio._enable_all()

    incompatible = [
        cheat
        for cheat in studio.collection.cheats
        if not cheat.compatible
    ]

    assert incompatible
    assert all(
        not cheat.enabled
        for cheat in incompatible
    )


def test_search_matches_name_category_type_and_code():
    app()

    studio = CheatStudio(
        game(),
        cheat_service=FakeService(),
    )

    studio.search.setText(
        "level"
    )
    assert [
        cheat.name
        for cheat in studio._filtered_cheats()
    ] == [
        "Level Select"
    ]

    studio.search.setText(
        "game_genie"
    )
    assert len(
        studio._filtered_cheats()
    ) == 3

    studio.search.setText(
        "AAAA-BBBB"
    )
    assert [
        cheat.name
        for cheat in studio._filtered_cheats()
    ] == [
        "Unlimited Lives"
    ]


def test_empty_collection_does_not_block_studio():
    app()

    service = FakeService()
    service.value.cheats = []

    studio = CheatStudio(
        game(),
        cheat_service=service,
    )

    assert studio.collection.cheats == []
    assert (
        studio.without_button.text()
        == "Continue Without Cheats"
    )


def test_runtime_file_serializes_only_enabled_compatible(
    tmp_path,
):
    service = CheatService(
        roots=[],
        user_root=tmp_path / "user",
    )

    cheats = [
        CheatCode(
            name="Enabled",
            code="AAAA",
            enabled=True,
            compatible=True,
        ),
        CheatCode(
            name="Disabled",
            code="BBBB",
            enabled=False,
            compatible=True,
        ),
        CheatCode(
            name="Incompatible",
            code="CCCC",
            enabled=True,
            compatible=False,
        ),
    ]

    runtime = Path(
        service.runtime_file(
            cheats
        )
    )

    text = runtime.read_text()

    assert "Enabled" in text
    assert "AAAA" in text
    assert "Disabled" not in text
    assert "BBBB" not in text
    assert "Incompatible" not in text
    assert "CCCC" not in text


def test_runtime_file_empty_selection_returns_empty():
    service = CheatService(
        roots=[],
    )

    assert service.runtime_file([]) == ""


def test_cheat_runtime_append_config_is_ephemeral(
    tmp_path,
):
    info_root = (
        tmp_path
        / "info"
    )
    info_root.mkdir()

    (
        info_root
        / "snes9x_libretro.info"
    ).write_text(
        'corename = "Snes9x"\n',
        encoding="utf-8",
    )

    cheat_file = (
        tmp_path
        / "game.cht"
    )

    cheat_file.write_text(
        'cheats = 1\n'
        'cheat0_desc = "Lives"\n'
        'cheat0_code = "AAAA"\n'
        'cheat0_enable = true\n',
        encoding="utf-8",
    )

    runtime = CheatRuntimeConfig(
        runtime_root=(
            tmp_path
            / "runtime"
        ),
        info_roots=(
            info_root,
        ),
    )

    config = Path(
        runtime.create(
            cheat_file,
            "/cores/snes9x_libretro.so",
            "/runtime/Game (USA).sfc",
        )
    )

    assert config.is_file()

    text = config.read_text(
        encoding="utf-8"
    )

    assert (
        "cheat_database_path"
        in text
    )

    assert (
        'apply_cheats_after_load = "true"'
        in text
    )

    assert (
        "cheat_file ="
        not in text
    )

    assert (
        "cheat_apply_after_load"
        not in text
    )

    runtime_cheat = (
        config.parent
        / "database"
        / "Snes9x"
        / "Game (USA).cht"
    )

    assert runtime_cheat.is_file()

    assert (
        runtime_cheat.read_text(
            encoding="utf-8"
        )
        == cheat_file.read_text(
            encoding="utf-8"
        )
    )


def test_launch_profile_accepts_cheat_file():
    profile = LaunchProfile(
        game="Example",
        rom="/games/example.nes",
        core="/cores/example.so",
        cheat_file="/tmp/example.cht",
    )

    assert (
        profile.cheat_file
        == "/tmp/example.cht"
    )
