"""Shared intent/launch authority contracts, independent of host installations."""
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from services.library.identity import game_identity
from services.library.presentation_studio import LibraryPresentationStudioService
from services.presentation.assets import PresentationAssetReferenceResolver
from services.presentation.composer import PresentationRecommendationComposer
from services.presentation.effective_resolver import EffectivePresentationResolver
from services.presentation.launch_resolver import LaunchPresentationResolver
from services.presentation.models import PresentationProfile
from services.presentation.production_package_resolver import CanonicalProductionPackageResolver
from services.presentation.recommendation_resolver import PresentationRecommendationResolver
from services.presentation.recommendations import PresentationRecommendationCatalog
from services.presentation.resolver import PresentationResolver

NES = 'platform.nintendo.nes'


def game(platform=NES, core='fceumm', local_id='local-file:edition-a'):
    return SimpleNamespace(name='Example', core=core, rvdb_platform_id=platform,
                           rvdb_game_id='game.example', local_file_id=local_id,
                           rom='/roms/example.nes')


def config(root):
    return {'paths': {kind: {'directory': str(root / kind)} for kind in ('overlays', 'shaders', 'artwork')}}


def package(root, platform=NES):
    settings = config(root)
    assets = CanonicalProductionPackageResolver._ASSETS[platform]
    overlay = root / 'overlays' / assets.overlay
    shader = root / 'shaders' / assets.shader
    for path in (overlay, shader):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# fixture\n')
    overlay.with_suffix('.runtime.cfg').write_text('# fixture\n')
    overlay.with_suffix('.production.json').write_text(json.dumps({'platform_id': platform}))
    return settings, overlay, shader


def intent(settings, manual=None, automatic=None, game_automatic=None):
    assets = PresentationAssetReferenceResolver(**{
        'shader_root': settings['paths']['shaders']['directory'],
        'overlay_root': settings['paths']['overlays']['directory'],
        'artwork_root': settings['paths']['artwork']['directory'],
    })
    recommendations = PresentationRecommendationResolver(
        catalog=PresentationRecommendationCatalog(automatic or {}, game_recommendations=game_automatic),
        asset_resolver=assets)
    return EffectivePresentationResolver(manual_resolver=manual or PresentationResolver(),
        recommendation_composer=PresentationRecommendationComposer(recommendation_resolver=recommendations),
        asset_resolver=assets)


def test_unused_recommendations_do_not_invalidate_manual_fields(tmp_path):
    manual = PresentationProfile(shader='/manual/shader', overlay='/manual/overlay', artwork='/manual/art')
    resolver = intent(config(tmp_path), PresentationResolver(default=manual),
                      {NES: PresentationProfile(shader='retro-vault://shaders/missing', overlay='retro-vault://overlays/missing')})
    assert resolver.resolve(game()) == manual
    assert resolver.references_with_sources(game())[0] == manual


def test_selected_missing_recommendation_remains_an_error(tmp_path):
    resolver = intent(config(tmp_path), automatic={NES: PresentationProfile(shader='retro-vault://shaders/missing')})
    with pytest.raises(ValueError, match='does not exist'):
        resolver.resolve(game())


def test_field_sources_follow_the_same_precedence_as_values(tmp_path):
    selected = game()
    manual = PresentationResolver(default=PresentationProfile(shader='default'),
        systems={NES: PresentationProfile(overlay='system')},
        games={game_identity(selected): PresentationProfile(shader='edition')})
    resolver = intent(config(tmp_path), manual,
        {NES: PresentationProfile(artwork='system-art')},
        {'game.example': PresentationProfile(artwork='game-art')})
    profile, sources = resolver.references_with_sources(selected)
    assert profile == resolver.resolve(selected) == PresentationProfile('edition', 'system', 'game-art')
    assert sources == {'shader': 'game', 'overlay': 'platform', 'artwork': 'game recommendation'}
    assert resolver.resolve(game(local_id='local-file:edition-b')).shader == 'default'


def test_package_supersedes_unavailable_preferences_without_resolving_them(tmp_path):
    settings, overlay, shader = package(tmp_path)
    requested = PresentationProfile(shader='retro-vault://shaders/deleted', overlay='/foreign/overlay')
    resolver = LaunchPresentationResolver(config=settings,
        intent_resolver=intent(settings, PresentationResolver(default=requested)))
    decision = resolver.describe(game())
    assert decision.available and decision.authority == 'production package'
    assert decision.requested == requested
    assert resolver.resolve(game()) == PresentationProfile(shader=str(shader), overlay=str(overlay))
    assert decision.package.overlay == str(overlay)


@pytest.mark.parametrize('platform,core,message', [
    ('platform.nintendo.n64','mupen64plus_next','not configured'),
    (NES,'snes9x','core'),
])
def test_policy_failures_are_visible_and_fail_closed(tmp_path, platform, core, message):
    settings, _, _ = package(tmp_path)
    resolver = LaunchPresentationResolver(config=settings, intent_resolver=intent(settings))
    decision = resolver.describe(game(platform, core))
    assert not decision.available
    assert message in decision.error.lower()
    with pytest.raises(ValueError):
        resolver.resolve(game(platform, core))


def test_missing_configured_package_does_not_fall_back_to_host_install(tmp_path):
    resolver = LaunchPresentationResolver(config=config(tmp_path), intent_resolver=intent(config(tmp_path)))
    decision = resolver.describe(game())
    assert not decision.available
    assert str(tmp_path) in decision.error


def test_unknown_platform_preserves_manual_semantics(tmp_path):
    requested = PresentationProfile(shader='/legacy/shader', overlay='/legacy/overlay')
    resolver = LaunchPresentationResolver(config=config(tmp_path),
        intent_resolver=intent(config(tmp_path), PresentationResolver(default=requested)))
    decision = resolver.describe(game('platform.legacy'))
    assert decision.available and decision.authority == 'manual'
    assert decision.selected == requested


def test_roots_and_symlinks_resolve_the_installed_package(tmp_path):
    settings, overlay, shader = package(tmp_path / 'installed')
    alias = tmp_path / 'overlay-alias'
    alias.symlink_to(overlay.parents[3], target_is_directory=True)
    settings['paths']['overlays']['directory'] = str(alias)
    selected = CanonicalProductionPackageResolver.resolve(platform_id=NES, core_identity='fceumm', config=settings)
    assert selected.overlay == str(overlay)
    assert selected.shader == str(shader)


def test_studio_reports_selected_package_and_preserves_saved_preferences(tmp_path):
    settings, overlay, _ = package(tmp_path)
    requested = PresentationProfile(overlay='/saved/preference')
    resolver = LaunchPresentationResolver(config=settings,
        intent_resolver=intent(settings, PresentationResolver(default=requested)))
    store = SimpleNamespace(load=lambda: {'default': requested, 'systems': {}, 'games': {}})
    state = LibraryPresentationStudioService(store, lambda: resolver).state_for(game())
    assert state.default_profile == requested
    assert state.overlay == str(overlay)
    assert state.source_label == 'Production Package'
    assert state.launch_decision.requested.overlay == requested.overlay


def test_launcher_revalidates_the_same_selection_before_runtime(tmp_path, monkeypatch):
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import RetroArchLauncher
    from services.retroarch.validator import LaunchValidator
    settings, overlay, _ = package(tmp_path / 'first')
    other, second_overlay, _ = package(tmp_path / 'second')
    observed = []
    def primary(**kwargs):
        observed.append(kwargs['overlay'])
        raise ValueError('stop before runtime')
    for method in ('check_retroarch', 'check_core', 'check_rom'):
        monkeypatch.setattr(LaunchValidator, method, lambda *args: True)
    spawn = Mock()
    monkeypatch.setattr('services.retroarch.launcher.subprocess.Popen', spawn)
    launcher = RetroArchLauncher(presentation_config_provider=lambda: settings,
        archive_runtime=SimpleNamespace(resolve=lambda rom, **kw: rom),
        primary_config_runtime=SimpleNamespace(create=primary, cleanup=lambda *args: None))
    profile = LaunchProfile('Example', '/rom', 'fceumm', platform_id=NES)
    launcher.launch(profile)
    settings = other
    launcher.launch(profile)
    assert observed == [str(overlay), str(second_overlay)]
    spawn.assert_not_called()


def test_resolution_does_not_install_spawn_or_write(tmp_path, monkeypatch):
    settings, _, _ = package(tmp_path)
    resolver = LaunchPresentationResolver(config=settings, intent_resolver=intent(settings))
    before = {p: p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    monkeypatch.setattr('subprocess.Popen', Mock(side_effect=AssertionError('spawn')))
    monkeypatch.setattr(Path, 'write_text', Mock(side_effect=AssertionError('write')))
    assert resolver.describe(game()).available
    assert {p: p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()} == before


def test_genesis_native_overlay_install_and_shader_assignment_reference(tmp_path):
    from services.presentation.native_deployment import NativeVisualDeploymentService
    from services.presentation.native_shader_deployment import NativeShaderDeploymentService
    from services.presentation.visual_manifest import VisualAssetCatalogManifest
    assets = {a.id: a for a in VisualAssetCatalogManifest().load().all()}
    overlay = assets['rvv.overlay.genesis.classic']
    service = NativeVisualDeploymentService(repository_root=Path.cwd(), overlay_root=tmp_path/'overlays')
    service.deploy(overlay)
    shader = assets['rvv.shader.genesis.classic.crt']
    shader_service = NativeShaderDeploymentService(repository_root=Path.cwd(), shader_root=tmp_path/'shaders')
    plan = shader_service.plan(shader)
    shader_service.deploy(shader)
    resolver = PresentationAssetReferenceResolver(overlay_root=tmp_path/'overlays', shader_root=tmp_path/'shaders')
    assert Path(resolver.resolve_reference(overlay.reference)).is_file()
    assert resolver.resolve_reference(plan.assignment_reference) == str(plan.destination_preset)
    selected = CanonicalProductionPackageResolver.resolve(platform_id='platform.sega.genesis',
        core_identity='genesis_plus_gx', config=config(tmp_path))
    assert selected.shader == str(plan.destination_preset)


def test_studio_widget_shows_launch_authority_and_can_clear_saved_preference(tmp_path):
    from PyQt6.QtWidgets import QApplication
    from services.presentation.store import PresentationStore
    from ui.library.widgets.presentation_studio import PresentationStudio
    app = QApplication.instance() or QApplication([])
    settings, overlay, _ = package(tmp_path)
    selected = game()
    store = PresentationStore(tmp_path / 'presentation.json')
    store.assign_game_overlay(game_identity(selected), '/saved/overlay')
    def provider():
        return LaunchPresentationResolver(config=settings, intent_resolver=intent(settings, store.resolver()))
    widget = PresentationStudio(presentation_store=store, presentation_resolver_provider=provider)
    widget.set_game(selected)
    assert widget.current_state.overlay == str(overlay)
    assert 'qualified platform package' in widget.game_override.text()
    assert not widget.use_overlay_button.isEnabled()
    assert widget.clear_overlay_button.isEnabled()
    widget.clear_game_overlay()
    assert not store.load()['games'].get(game_identity(selected), PresentationProfile()).overlay
    assert widget.current_state.overlay == str(overlay)
    widget.close()


def test_factory_uses_one_configuration_snapshot_for_selection(tmp_path, monkeypatch):
    from config import ConfigLoader
    from services.presentation.factory import PresentationCompositionFactory
    from services.presentation.manifest import PresentationRecommendationManifest
    from services.presentation.store import PresentationStore
    settings, overlay, _ = package(tmp_path)
    loader = ConfigLoader()
    load = Mock(return_value=settings)
    monkeypatch.setattr(loader, 'load', load)
    factory = PresentationCompositionFactory(presentation_store=PresentationStore(tmp_path/'store.json'),
        config_loader=loader, recommendation_manifest=PresentationRecommendationManifest())
    resolver = factory.build_launch()
    load.assert_called_once()
    assert resolver.resolve(game()).overlay == str(overlay)


@pytest.mark.parametrize('settings', [None, {'paths': []}, {'paths': {'overlays': None}}, {'paths': {'overlays': {'directory': ''}}}])
def test_invalid_or_missing_configured_roots_do_not_silently_fall_back(tmp_path, settings):
    if settings is None:
        settings = config(tmp_path)
        settings['paths'].pop('overlays')
    with pytest.raises(ValueError):
        CanonicalProductionPackageResolver.resolve(platform_id=NES, core_identity='fceumm', config=settings)


def test_native_visuals_page_uses_launch_selection_and_reports_unavailable(tmp_path):
    from PyQt6.QtWidgets import QApplication
    from services.presentation.store import PresentationStore
    from ui.pages.visuals_page import NativeVisualsPage
    app = QApplication.instance() or QApplication([])
    settings, overlay, _ = package(tmp_path)
    store = PresentationStore(tmp_path/'store.json')
    store.assign_default_overlay('/saved/overlay')
    selected = game()
    page = NativeVisualsPage(native_visual_service=SimpleNamespace(native_assets=lambda: []),
        presentation_store=store, current_game_provider=lambda: selected,
        presentation_resolver_provider=lambda: LaunchPresentationResolver(
            config=settings, intent_resolver=intent(settings, store.resolver())))
    page._refresh_assignment_state()
    assert page.default_assignment_value.text() == 'Default: /saved/overlay'
    assert page.effective_assignment_value.text() == 'Launch: ' + str(overlay)
    overlay.unlink()
    page._refresh_assignment_state()
    assert 'unavailable' in page.effective_assignment_value.text()
    assert store.load()['default'].overlay == '/saved/overlay'
    page.close()


def test_legacy_preview_does_not_require_core_selection(tmp_path):
    requested = PresentationProfile(overlay='/legacy/overlay')
    resolver = LaunchPresentationResolver(config=config(tmp_path),
        intent_resolver=intent(config(tmp_path), PresentationResolver(default=requested)))
    assert resolver.resolve(game('', core='')) == requested


def test_package_symlink_cannot_escape_configured_asset_root(tmp_path):
    settings, _, _ = package(tmp_path / 'external')
    configured = tmp_path / 'configured'
    configured.mkdir()
    (configured/'retrovault').symlink_to(tmp_path/'external/overlays/retrovault', target_is_directory=True)
    settings['paths']['overlays']['directory'] = str(configured)
    with pytest.raises(ValueError, match='escapes'):
        CanonicalProductionPackageResolver.resolve(platform_id=NES, core_identity='fceumm', config=settings)


@pytest.mark.parametrize('platform', [
    'platform.sega.master.system', 'platform.sega.game.gear', 'platform.sega.sg1000'])
def test_shared_genesis_core_does_not_grant_genesis_production_package(tmp_path, platform):
    settings, overlay, shader = package(tmp_path, 'platform.sega.genesis')
    request = PresentationProfile(overlay=str(overlay), shader=str(shader))
    resolver = LaunchPresentationResolver(config=settings,
        intent_resolver=intent(settings, PresentationResolver(default=request)))
    decision = resolver.describe(game(platform, core='genesis_plus_gx'))
    assert not decision.available
    assert 'not configured' in decision.error
    assert decision.selected == PresentationProfile()
    assert decision.requested == request
