import json

import pytest
import yaml

from config import ConfigLoader
from services.library.models import Game
from services.presentation import (
    EffectivePresentationResolver,
    PresentationCompositionFactory,
    PresentationProfile,
    PresentationRecommendationManifest,
    PresentationStore,
)


NES = "platform.nintendo.nes"


def make_game(
    tmp_path,
):
    return Game(
        name="Duck Tales 2",
        platform="Nintendo Entertainment System",
        year=1993,
        genre="Platform",
        core="FCEUmm",
        rom=str(
            tmp_path
            / "Duck Tales 2 (U).nes"
        ),
        rvdb_platform_id=NES,
    )


def write_manifest(
    tmp_path,
    *,
    shader="",
    overlay="",
    artwork="",
):
    path = (
        tmp_path
        / "recommendations.json"
    )

    path.write_text(
        json.dumps(
            {
                "version": 1,
                "systems": {
                    NES: {
                        "shader": shader,
                        "overlay": overlay,
                        "artwork": artwork,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    return path


def write_defaults(
    tmp_path,
    *,
    shaders,
    overlays,
    artwork,
):
    path = tmp_path / "defaults.yaml"

    path.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "shaders": {
                        "directory": str(shaders),
                    },
                    "overlays": {
                        "directory": str(overlays),
                    },
                    "artwork": {
                        "directory": str(artwork),
                    },
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    return path


def make_factory(
    tmp_path,
    *,
    manifest_file,
    defaults_file,
    runtime_file=None,
    store=None,
):
    loader = ConfigLoader(
        default_file=defaults_file,
        runtime_file=(
            runtime_file
            or (
                tmp_path
                / "missing-runtime.json"
            )
        ),
    )

    return PresentationCompositionFactory(
        presentation_store=(
            store
            or PresentationStore(
                tmp_path
                / "presentation-state.json"
            )
        ),
        config_loader=loader,
        recommendation_manifest=(
            PresentationRecommendationManifest(
                manifest_file
            )
        ),
    )


def create_asset(
    root,
    relative,
):
    path = root / relative

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        "asset",
        encoding="utf-8",
    )

    return path.resolve()


def test_factory_builds_effective_resolver_from_configured_roots(
    tmp_path,
):
    shaders = tmp_path / "shaders"
    overlays = tmp_path / "overlays"
    artwork = tmp_path / "artwork"

    shaders.mkdir()
    overlays.mkdir()
    artwork.mkdir()

    shader = create_asset(
        shaders,
        f"{NES}/default.slangp",
    )
    overlay = create_asset(
        overlays,
        f"{NES}/default.cfg",
    )
    image = create_asset(
        artwork,
        f"{NES}/default.png",
    )

    manifest = write_manifest(
        tmp_path,
        shader=(
            "retro-vault://shaders/"
            f"{NES}/default.slangp"
        ),
        overlay=(
            "retro-vault://overlays/"
            f"{NES}/default.cfg"
        ),
        artwork=(
            "retro-vault://artwork/"
            f"{NES}/default.png"
        ),
    )

    defaults = write_defaults(
        tmp_path,
        shaders=shaders,
        overlays=overlays,
        artwork=artwork,
    )

    factory = make_factory(
        tmp_path,
        manifest_file=manifest,
        defaults_file=defaults,
    )

    resolver = factory.build()

    assert isinstance(
        resolver,
        EffectivePresentationResolver,
    )

    assert resolver.resolve(
        make_game(tmp_path)
    ) == PresentationProfile(
        shader=str(shader),
        overlay=str(overlay),
        artwork=str(image),
    )


def test_factory_preserves_manual_assignments_over_recommendations(
    tmp_path,
):
    shaders = tmp_path / "shaders"
    overlays = tmp_path / "overlays"
    artwork = tmp_path / "artwork"

    shaders.mkdir()
    overlays.mkdir()
    artwork.mkdir()

    shader = create_asset(
        shaders,
        f"{NES}/default.slangp",
    )

    create_asset(
        overlays,
        f"{NES}/default.cfg",
    )

    manifest = write_manifest(
        tmp_path,
        shader=(
            "retro-vault://shaders/"
            f"{NES}/default.slangp"
        ),
        overlay=(
            "retro-vault://overlays/"
            f"{NES}/default.cfg"
        ),
    )

    defaults = write_defaults(
        tmp_path,
        shaders=shaders,
        overlays=overlays,
        artwork=artwork,
    )

    store = PresentationStore(
        tmp_path
        / "presentation-state.json"
    )

    store.save(
        systems={
            NES: PresentationProfile(
                overlay="/manual/nes.cfg",
            ),
        }
    )

    factory = make_factory(
        tmp_path,
        manifest_file=manifest,
        defaults_file=defaults,
        store=store,
    )

    assert factory.build().resolve(
        make_game(tmp_path)
    ) == PresentationProfile(
        shader=str(shader),
        overlay="/manual/nes.cfg",
    )


def test_factory_reloads_runtime_configuration_on_each_build(
    tmp_path,
):
    first = tmp_path / "first-shaders"
    second = tmp_path / "second-shaders"
    overlays = tmp_path / "overlays"
    artwork = tmp_path / "artwork"

    first.mkdir()
    second.mkdir()
    overlays.mkdir()
    artwork.mkdir()

    first_shader = create_asset(
        first,
        f"{NES}/default.slangp",
    )
    second_shader = create_asset(
        second,
        f"{NES}/default.slangp",
    )

    manifest = write_manifest(
        tmp_path,
        shader=(
            "retro-vault://shaders/"
            f"{NES}/default.slangp"
        ),
    )

    defaults = write_defaults(
        tmp_path,
        shaders=first,
        overlays=overlays,
        artwork=artwork,
    )

    runtime = tmp_path / "runtime.json"

    factory = make_factory(
        tmp_path,
        manifest_file=manifest,
        defaults_file=defaults,
        runtime_file=runtime,
    )

    game = make_game(tmp_path)

    assert factory.build().resolve(
        game
    ).shader == str(first_shader)

    runtime.write_text(
        json.dumps(
            {
                "paths": {
                    "shaders": {
                        "directory": str(second),
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    assert factory.build().resolve(
        game
    ).shader == str(second_shader)


def test_factory_reloads_manual_presentation_on_each_build(
    tmp_path,
):
    shaders = tmp_path / "shaders"
    overlays = tmp_path / "overlays"
    artwork = tmp_path / "artwork"

    shaders.mkdir()
    overlays.mkdir()
    artwork.mkdir()

    shader = create_asset(
        shaders,
        f"{NES}/default.slangp",
    )

    manifest = write_manifest(
        tmp_path,
        shader=(
            "retro-vault://shaders/"
            f"{NES}/default.slangp"
        ),
    )

    defaults = write_defaults(
        tmp_path,
        shaders=shaders,
        overlays=overlays,
        artwork=artwork,
    )

    store = PresentationStore(
        tmp_path
        / "presentation-state.json"
    )

    factory = make_factory(
        tmp_path,
        manifest_file=manifest,
        defaults_file=defaults,
        store=store,
    )

    game = make_game(tmp_path)

    assert factory.build().resolve(
        game
    ).shader == str(shader)

    store.assign_system_shader(
        NES,
        "/manual/new.slangp",
    )

    assert factory.build().resolve(
        game
    ).shader == "/manual/new.slangp"


def test_blank_configured_root_remains_unconfigured_until_used(
    tmp_path,
):
    overlays = tmp_path / "overlays"
    artwork = tmp_path / "artwork"

    overlays.mkdir()
    artwork.mkdir()

    manifest = write_manifest(
        tmp_path,
        shader=(
            "retro-vault://shaders/"
            f"{NES}/default.slangp"
        ),
    )

    defaults = write_defaults(
        tmp_path,
        shaders="",
        overlays=overlays,
        artwork=artwork,
    )

    factory = make_factory(
        tmp_path,
        manifest_file=manifest,
        defaults_file=defaults,
    )

    with pytest.raises(
        ValueError,
        match=(
            "No local presentation asset root "
            "configured for shaders"
        ),
    ):
        factory.build().resolve(
            make_game(tmp_path)
        )


def test_empty_manifest_does_not_require_asset_directories(
    tmp_path,
):
    manifest = tmp_path / "recommendations.json"

    manifest.write_text(
        json.dumps(
            {
                "version": 1,
                "systems": {},
            }
        ),
        encoding="utf-8",
    )

    defaults = write_defaults(
        tmp_path,
        shaders="",
        overlays="",
        artwork="",
    )

    factory = make_factory(
        tmp_path,
        manifest_file=manifest,
        defaults_file=defaults,
    )

    assert factory.build().resolve(
        make_game(tmp_path)
    ) == PresentationProfile()


def test_non_string_configured_directory_is_rejected(
    tmp_path,
):
    manifest = tmp_path / "recommendations.json"

    manifest.write_text(
        json.dumps(
            {
                "version": 1,
                "systems": {},
            }
        ),
        encoding="utf-8",
    )

    defaults = tmp_path / "defaults.yaml"

    defaults.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "shaders": {
                        "directory": 123,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    factory = make_factory(
        tmp_path,
        manifest_file=manifest,
        defaults_file=defaults,
    )

    with pytest.raises(
        ValueError,
        match="must be a string",
    ):
        factory.build()


@pytest.mark.parametrize(
    "presentation_store",
    [
        None,
        {},
        "",
    ],
)
def test_constructor_requires_presentation_store(
    tmp_path,
    presentation_store,
):
    with pytest.raises(
        TypeError,
        match="Presentation store",
    ):
        PresentationCompositionFactory(
            presentation_store=(
                presentation_store
            ),
            config_loader=ConfigLoader(
                runtime_file=(
                    tmp_path
                    / "missing-runtime.json"
                )
            ),
            recommendation_manifest=(
                PresentationRecommendationManifest()
            ),
        )


@pytest.mark.parametrize(
    "config_loader",
    [
        None,
        {},
        "",
    ],
)
def test_constructor_requires_config_loader(
    tmp_path,
    config_loader,
):
    with pytest.raises(
        TypeError,
        match="Configuration loader",
    ):
        PresentationCompositionFactory(
            presentation_store=(
                PresentationStore(
                    tmp_path
                    / "presentation-state.json"
                )
            ),
            config_loader=config_loader,
            recommendation_manifest=(
                PresentationRecommendationManifest()
            ),
        )


@pytest.mark.parametrize(
    "recommendation_manifest",
    [
        None,
        {},
        "",
    ],
)
def test_constructor_requires_recommendation_manifest(
    tmp_path,
    recommendation_manifest,
):
    with pytest.raises(
        TypeError,
        match="Recommendation manifest",
    ):
        PresentationCompositionFactory(
            presentation_store=(
                PresentationStore(
                    tmp_path
                    / "presentation-state.json"
                )
            ),
            config_loader=ConfigLoader(
                runtime_file=(
                    tmp_path
                    / "missing-runtime.json"
                )
            ),
            recommendation_manifest=(
                recommendation_manifest
            ),
        )
