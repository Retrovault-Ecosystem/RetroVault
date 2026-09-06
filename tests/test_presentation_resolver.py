from services.library.models import Game
from services.library.state import game_identity
from services.presentation import (
    PresentationProfile,
    PresentationResolver,
)


def make_game(
    tmp_path,
    *,
    platform_id="platform.nintendo.nes",
):
    rom = (
        tmp_path
        / "Duck Tales 2 (U).nes"
    )

    return Game(
        name="Duck Tales 2",
        platform="Nintendo Entertainment System",
        year=1993,
        genre="Platform",
        core="FCEUmm",
        rom=str(rom),
        rvdb_platform_id=platform_id,
    )


def test_resolver_returns_empty_profile_without_assignments(
    tmp_path,
):
    game = make_game(
        tmp_path
    )

    resolver = PresentationResolver()

    assert resolver.resolve(
        game
    ) == PresentationProfile()


def test_default_profile_applies_without_more_specific_assignment(
    tmp_path,
):
    game = make_game(
        tmp_path
    )

    resolver = PresentationResolver(
        default=PresentationProfile(
            shader="/presentation/default.slangp",
            overlay="/presentation/default.cfg",
            artwork="/presentation/default.png",
        )
    )

    assert resolver.resolve(
        game
    ) == PresentationProfile(
        shader="/presentation/default.slangp",
        overlay="/presentation/default.cfg",
        artwork="/presentation/default.png",
    )


def test_system_assignment_overrides_individual_default_fields(
    tmp_path,
):
    game = make_game(
        tmp_path
    )

    resolver = PresentationResolver(
        default=PresentationProfile(
            shader="/presentation/default.slangp",
            overlay="/presentation/default.cfg",
            artwork="/presentation/default.png",
        ),
        systems={
            "platform.nintendo.nes": (
                PresentationProfile(
                    shader="/presentation/nes.slangp",
                )
            ),
        },
    )

    assert resolver.resolve(
        game
    ) == PresentationProfile(
        shader="/presentation/nes.slangp",
        overlay="/presentation/default.cfg",
        artwork="/presentation/default.png",
    )


def test_game_assignment_overrides_system_by_property(
    tmp_path,
):
    game = make_game(
        tmp_path
    )

    identity = game_identity(
        game
    )

    resolver = PresentationResolver(
        default=PresentationProfile(
            artwork="/presentation/default.png",
        ),
        systems={
            "platform.nintendo.nes": (
                PresentationProfile(
                    shader="/presentation/nes.slangp",
                    overlay="/presentation/nes.cfg",
                )
            ),
        },
        games={
            identity: PresentationProfile(
                overlay="/presentation/duck-tales-2.cfg",
            ),
        },
    )

    assert resolver.resolve(
        game
    ) == PresentationProfile(
        shader="/presentation/nes.slangp",
        overlay="/presentation/duck-tales-2.cfg",
        artwork="/presentation/default.png",
    )


def test_game_without_rom_can_still_inherit_system_assignment():
    game = Game(
        name="Placeholder Game",
        platform="Nintendo Entertainment System",
        year=0,
        genre="",
        core="FCEUmm",
        rom="",
        rvdb_platform_id=(
            "platform.nintendo.nes"
        ),
    )

    resolver = PresentationResolver(
        default=PresentationProfile(
            artwork="/presentation/default.png",
        ),
        systems={
            "platform.nintendo.nes": (
                PresentationProfile(
                    shader="/presentation/nes.slangp",
                )
            ),
        },
    )

    assert resolver.resolve(
        game
    ) == PresentationProfile(
        shader="/presentation/nes.slangp",
        artwork="/presentation/default.png",
    )
