import ast
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



def test_rvv_assignment_store_is_same_store_used_by_runtime_factory():
    source = Path(
        "ui/main_window.py"
    ).read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source
    )

    main_window = next(
        node
        for node in tree.body
        if (
            isinstance(node, ast.ClassDef)
            and node.name == "MainWindow"
        )
    )

    init = next(
        node
        for node in main_window.body
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "__init__"
        )
    )

    init_source = ast.get_source_segment(
        source,
        init,
    )

    assert (
        init_source.count(
            "presentation_store = PresentationStore()"
        )
        == 1
    )

    factory_index = init_source.index(
        "PresentationCompositionFactory("
    )

    visual_index = init_source.index(
        '"RetroVault Visuals"'
    )

    factory_surface = init_source[
        factory_index:
        visual_index
    ]

    assert (
        "presentation_store=(\n"
        "                    presentation_store"
        in factory_surface
    )

    visual_surface = init_source[
        visual_index:
    ]

    assert (
        "presentation_store=(\n"
        "                    presentation_store"
        in visual_surface
    )


def test_runtime_launch_uses_production_composition_factory_after_rvv_assignment():
    main_source = Path(
        "ui/main_window.py"
    ).read_text(
        encoding="utf-8"
    )

    factory_source = Path(
        "services/presentation/factory.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "PresentationCompositionFactory("
        in main_source
    )

    assert (
        "presentation_resolver_provider=(\n"
        "                presentation_composition_factory.build"
        in main_source
    )

    assert (
        "self.presentation_store.resolver()"
        in factory_source
    )


def test_rvv_does_not_create_parallel_runtime_presentation_store():
    main_source = Path(
        "ui/main_window.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        main_source.count(
            "presentation_store = PresentationStore()"
        )
        == 1
    )

    assert (
        "NativeVisualsPage("
        in main_source
    )

    assert (
        "presentation_composition_factory.build"
        in main_source
    )
