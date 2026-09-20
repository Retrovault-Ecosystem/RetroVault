import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PyQt6.QtWidgets import (
    QApplication,
)

from services.library.canonicalization import (
    LibraryCanonicalizer,
)
from services.library.models import Game
from ui.library.widgets.game_card import (
    GameCard,
)
from ui.library.widgets.game_edition_launcher import (
    GameEditionLauncher,
)


_QT_APP = None


def _app():
    global _QT_APP

    if _QT_APP is None:
        _QT_APP = (
            QApplication.instance()
            or QApplication([])
        )

    return _QT_APP


def make_game(filename):
    return Game(
        name=filename.rsplit(
            ".",
            1,
        )[0],
        platform=(
            "Nintendo Entertainment System"
        ),
        year=0,
        genre="",
        core="nestopia",
        rom=f"/validation/{filename}",
        source="Validation",
        rvdb_platform_id="platform.nes",
    )


def make_family():
    games = [
        make_game(
            "Example Game (USA).nes"
        ),
        make_game(
            "Example Game (USA) (Rev 1).nes"
        ),
        make_game(
            "Example Game (J) [T+Eng].nes"
        ),
        make_game(
            "Example Game (Japan).nes"
        ),
        make_game(
            "Example Game (USA) [h1].nes"
        ),
        make_game(
            "Example Game (USA) (Proto).nes"
        ),
        make_game(
            "Example Game (USA) (Unl).nes"
        ),
    ]

    visible = (
        LibraryCanonicalizer()
        .canonicalize(games)
    )

    assert len(visible) == 1

    return visible[0]


def test_launcher_requires_selection_only_for_multi_edition_family():
    single = make_game(
        "Singleton Game (USA).nes"
    )

    family = make_family()

    assert not (
        GameEditionLauncher
        .requires_selection(single)
    )

    assert (
        GameEditionLauncher
        .requires_selection(family)
    )


def test_launcher_groups_family_by_semantic_category():
    grouped = (
        GameEditionLauncher
        .grouped_variants(
            make_family()
        )
    )

    assert list(grouped) == [
        "standard",
        "revision",
        "translation",
        "region",
        "hack",
        "prototype",
        "unlicensed",
    ]

    assert all(
        len(grouped[category]) == 1
        for category in grouped
    )


def test_launcher_uses_professional_group_titles():
    expected = {
        "standard": "Standard Edition",
        "revision": "Revisions",
        "translation": (
            "Translations & Languages"
        ),
        "region": "Regional Editions",
        "hack": "Hacks & Mods",
        "prototype": (
            "Prototypes & Betas"
        ),
        "unlicensed": (
            "Unlicensed / Aftermarket"
        ),
    }

    for category, title in expected.items():
        assert (
            GameEditionLauncher
            .category_title(category)
            == title
        )


def test_launcher_preselects_preferred_standard_edition():
    _app()

    dialog = GameEditionLauncher(
        make_family()
    )

    checked = (
        dialog.button_group
        .checkedButton()
    )

    assert checked is not None

    variant = checked.property(
        "variantRecord"
    )

    assert variant["preferred"]
    assert (
        GameEditionLauncher
        ._category_key(
            variant["category"]
        )
        == "standard"
    )
    assert variant["rom"].endswith(
        "Example Game (USA).nes"
    )


def test_launcher_hides_empty_groups():
    games = [
        make_game(
            "Example Game (USA).nes"
        ),
        make_game(
            "Example Game (Japan).nes"
        ),
    ]

    family = (
        LibraryCanonicalizer()
        .canonicalize(games)[0]
    )

    grouped = (
        GameEditionLauncher
        .grouped_variants(family)
    )

    assert list(grouped) == [
        "standard",
        "region",
    ]


def test_launcher_semantic_object_names():
    _app()

    dialog = GameEditionLauncher(
        make_family()
    )

    assert (
        dialog.objectName()
        == "LibraryEditionLauncher"
    )

    assert (
        dialog.launch_button.objectName()
        == "LibraryEditionLaunch"
    )

    assert (
        dialog.cancel_button.objectName()
        == "LibraryEditionCancel"
    )

    assert (
        dialog.launch_button.text()
        == "▶ Launch Selected Edition"
    )


def test_singleton_fallback_variant_is_preferred_standard():
    game = make_game(
        "Singleton Game (USA).nes"
    )

    variants = (
        GameEditionLauncher
        .variants_for_game(game)
    )

    assert len(variants) == 1
    assert variants[0]["rom"] == game.rom
    assert variants[0]["preferred"]
    assert (
        variants[0]["category"]
        == "standard"
    )


def test_game_card_exposes_multi_edition_count():
    _app()

    card = GameCard(
        make_family()
    )

    assert (
        card.edition_count.objectName()
        == "LibraryGameEditionCount"
    )

    assert (
        card.edition_count.text()
        == "7 Editions"
    )

    assert not (
        card.edition_count.isHidden()
    )


def test_game_card_hides_singleton_edition_count():
    _app()

    card = GameCard(
        make_game(
            "Singleton Game (USA).nes"
        )
    )

    assert (
        card.edition_count.text()
        == ""
    )

    assert (
        card.edition_count.isHidden()
    )


def test_game_details_builds_physical_launch_target_without_mutating_family():
    _app()

    from ui.library.details.game_details import (
        GameDetails,
    )

    family = make_family()

    original_rom = family.rom
    original_name = family.name

    revision = next(
        variant
        for variant in family.variants
        if (
            GameEditionLauncher
            ._category_key(
                variant["category"]
            )
            == "revision"
        )
    )

    details = GameDetails()
    details.current_game = family

    launch_target = (
        details
        ._launch_target_from_variant(
            revision
        )
    )

    assert launch_target is not family
    assert (
        launch_target.rom
        == revision["rom"]
    )
    assert (
        launch_target.name
        == revision["name"]
    )
    assert (
        launch_target.variant_category
        == "revision"
    )

    assert family.rom == original_rom
    assert family.name == original_name


def test_game_details_singleton_launch_target_uses_original_rom():
    _app()

    from ui.library.details.game_details import (
        GameDetails,
    )

    game = make_game(
        "Singleton Game (USA).nes"
    )

    variant = (
        GameEditionLauncher
        .variants_for_game(game)[0]
    )

    details = GameDetails()
    details.current_game = game

    launch_target = (
        details
        ._launch_target_from_variant(
            variant
        )
    )

    assert launch_target.rom == game.rom


def test_launcher_normalizes_a7_category_titles_to_stable_keys():
    cases = {
        "Standard Edition": "standard",
        "Revisions": "revision",
        "Translations & Languages": (
            "translation"
        ),
        "Regional Editions": "region",
        "Hacks & Mods": "hack",
        "Prototypes & Betas": (
            "prototype"
        ),
        "Unlicensed / Aftermarket": (
            "unlicensed"
        ),
        "Other Variants": "other",
        "standard": "standard",
        "revision": "revision",
        "translation": "translation",
        "region": "region",
        "hack": "hack",
        "prototype": "prototype",
        "unlicensed": "unlicensed",
        "other": "other",
    }

    for source, expected in cases.items():
        assert (
            GameEditionLauncher
            ._category_key(source)
            == expected
        )
