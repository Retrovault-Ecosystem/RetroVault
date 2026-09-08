from pathlib import Path


def test_main_window_uses_production_presentation_factory():
    source = Path(
        "ui/main_window.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "PresentationCompositionFactory"
        in source
    )

    assert (
        "PresentationRecommendationManifest"
        in source
    )

    assert (
        "ConfigLoader()"
        in source
    )

    assert (
        "presentation_store=("
        in source
    )

    assert (
        "presentation_composition_factory.build"
        in source
    )


def test_main_window_no_longer_provides_raw_manual_resolver():
    source = Path(
        "ui/main_window.py"
    ).read_text(
        encoding="utf-8"
    )

    provider_block = (
        "presentation_resolver_provider=("
        "\n"
        "                "
        "presentation_composition_factory.build"
    )

    assert provider_block in source

    assert (
        "presentation_resolver_provider=("
        "\n"
        "                "
        "presentation_store.resolver"
        not in source
    )


def test_main_window_preserves_manual_store_for_assignment_pages():
    source = Path(
        "ui/main_window.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "presentation_store=("
        in source
    )

    assert (
        "OverlaysPage("
        in source
    )

    assert (
        "ShadersPage("
        in source
    )


def test_launcher_and_game_details_remain_outside_factory_wiring():
    main_window = Path(
        "ui/main_window.py"
    ).read_text(
        encoding="utf-8"
    )

    factory = Path(
        "services/presentation/factory.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "RetroArchLauncher" not in factory
    assert "LaunchProfile" not in factory
    assert "GameDetails" not in factory

    assert (
        "presentation_composition_factory.build"
        in main_window
    )
