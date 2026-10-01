"""Metadata identity and local covers must not become runtime/user-state authority."""
import json
from types import SimpleNamespace

import pytest

from services.artwork.service import ArtworkService
from services.library.models import Game
from services.library.rvdb_resolver import RVDBLibraryResolver
from services.library.scanner import RomScanner
from services.library.library_service import LibraryService
from services.library.canonicalization import LibraryCanonicalizer


@pytest.fixture
def resolver(tmp_path):
    nodes, edges = {}, {}
    for slug, extension in [('nes', 'nes'), ('snes', 'sfc'), ('genesis', 'md')]:
        pid = 'platform.' + slug
        nodes[pid] = dict(id=pid, type='platform', name=slug.upper(),
                          aliases=[slug, slug.upper()], extensions=[extension])
        gid = 'game.' + slug
        nodes[gid] = dict(id=gid, type='game', name='Same Game',
                          aliases=['same game', 'Same Game'], release_year=1991)
        edges[gid] = {'platform': [pid]}
    path = tmp_path / 'bundle.json'
    path.write_text(json.dumps({'nodes': nodes, 'edges': edges}))
    return RVDBLibraryResolver.from_bundle(path)


def game(tmp_path, slug='nes', title='Same Game (USA)', **values):
    result = Game(title, slug.upper(), 0, '', '', rom=str(tmp_path / (title + '.nes')),
                  rvdb_platform_id='platform.' + slug, rvdb_game_id='game.' + slug)
    for key, value in values.items():
        setattr(result, key, value)
    return result


def cover(root, folder, title):
    path = root / folder / (title + '.png')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'local cover lookup fixture')
    return path


@pytest.mark.parametrize('title', ['Same Game', 'Same Game (USA)', 'Same Game (Europe)',
                                   'Same Game (Rev 1)', 'Same Game (Japan) (Rev 2)'])
def test_unique_retail_metadata_and_duplicate_aliases(resolver, title):
    assert resolver.game_for_rom_name(title, 'platform.nes').id == 'game.nes'
    assert resolver.platform_for_name('NES').id == 'platform.nes'


@pytest.mark.parametrize('title', ['Same Game (Hack)', 'Same Game [h1]', 'Same Game [T+Eng]',
                                   'Same Game (Prototype)', 'Same Game (Demo)',
                                   'Same Game (Unlicensed)', 'Same Game (Unknown Tag)'])
def test_no_speculative_modified_title_match(resolver, title):
    assert resolver.game_for_rom_name(title, 'platform.nes') is None


def test_ambiguity_does_not_fall_back(resolver):
    original = resolver.service.game('game.nes')
    from dataclasses import replace
    resolver._game_name_map['same game (usa)'] = [original, replace(original, id='game.other')]
    assert resolver.game_for_rom_name('Same Game (USA)', 'platform.nes') is None


def test_scan_enriches_real_tagged_file_without_changing_path(resolver, tmp_path):
    rom = tmp_path / 'Same Game (USA).nes'
    rom.write_bytes(b'ROM fixture')
    result = RomScanner(rvdb_resolver=resolver).scan(SimpleNamespace(path=str(tmp_path), name='test'))
    assert len(result) == 1
    assert result[0].rvdb_game_id == 'game.nes'
    assert result[0].year == 1991
    assert result[0].rom == str(rom)


@pytest.mark.parametrize('folder', ['SNES', 'platform.snes', 'snes'])
def test_unique_foreign_platform_cover_is_rejected(resolver, tmp_path, folder):
    root = tmp_path / 'covers'
    cover(root, folder, 'Same Game (USA)')
    assert ArtworkService(root, resolver).get_artwork(game(tmp_path)) is None


def test_canonical_cover_platform_scope_and_exact_precedence(resolver, tmp_path):
    root = tmp_path / 'covers'
    expected = cover(root, 'platform.nes', 'Same Game')
    cover(root, 'SNES', 'Same Game')
    service = ArtworkService(root, resolver)
    g = game(tmp_path)
    assert service.get_artwork(g) == str(expected)
    exact = cover(root, 'NES', 'Same Game (USA)')
    service.invalidate()
    assert service.get_artwork(g) == str(exact)
    g.rvdb_game_id = ''
    exact.unlink()
    service.invalidate()
    assert service.get_artwork(g) is None


def test_cache_deletion_and_explicit_override(resolver, tmp_path):
    root = tmp_path / 'covers'
    first = cover(root, 'NES', 'Same Game (USA)')
    service = ArtworkService(root, resolver)
    g = game(tmp_path)
    g.artwork = service.get_artwork(g)
    first.unlink()
    assert service.get_artwork(g) is None
    explicit = cover(tmp_path, 'manual', 'chosen')
    g.artwork, g.artwork_origin = str(explicit), 'explicit'
    assert service.get_artwork(g) == str(explicit)
    service.set_directory(tmp_path / 'absent')
    assert service.get_artwork(g) == str(explicit)


def test_refresh_preserves_per_edition_covers_and_explicit_intent(resolver, tmp_path):
    root = tmp_path / 'covers'
    usa = game(tmp_path)
    europe = game(tmp_path, title='Same Game (Europe)')
    usa.local_file_id, europe.local_file_id = 'local-file:usa', 'local-file:europe'
    explicit = cover(tmp_path, 'manual', 'chosen')
    usa.artwork = str(explicit)
    first = cover(root, 'NES', 'Same Game (Europe)')
    service = LibraryService.__new__(LibraryService)
    service.artwork = ArtworkService(root, resolver)
    service.state = SimpleNamespace(favorites=lambda: {'local-file:europe'})
    service._physical_games = [usa, europe]
    service.games = LibraryCanonicalizer().canonicalize(service._physical_games)
    service.refresh_artwork(root)
    assert usa.artwork == str(explicit)
    assert europe.artwork == str(first)
    assert service.games[0].favorite
    records = {v['local_file_id']: v for v in service.games[0].variants}
    restored = service._variant_game_from_record(service.games[0], records['local-file:europe'])
    assert restored.artwork == str(first)
    second_root = tmp_path / 'new-covers'
    second = cover(second_root, 'NES', 'Same Game (Europe)')
    service.refresh_artwork(second_root)
    assert usa.artwork == str(explicit)
    assert europe.artwork == str(second)
    assert {v['local_file_id'] for v in service.games[0].variants} == set(records)


def test_fresh_process_rebuild_keeps_enrichment_and_user_state(resolver, tmp_path, monkeypatch):
    import os
    import subprocess
    import sys
    from pathlib import Path
    from config.writer import ConfigWriter
    from controllers.library_controller import LibraryController
    from services.library.import_sources import ImportSourceStore
    from services.library.presentation_studio import LibraryPresentationStudioService
    from services.presentation.store import PresentationStore

    for key, folder in [('XDG_CONFIG_HOME', 'profile'), ('XDG_CACHE_HOME', 'cache'), ('XDG_DATA_HOME', 'data')]:
        monkeypatch.setenv(key, str(tmp_path / folder))
    root = tmp_path / 'roms'
    root.mkdir()
    (root / 'Same Game (USA).nes').write_bytes(b'local test content')
    covers = tmp_path / 'covers'
    expected_cover = cover(covers, 'NES', 'Same Game')
    ConfigWriter().write({'library': {'sources': []}, 'paths': {'artwork': {'directory': str(covers)}}})
    ImportSourceStore().persist_directory(root, source_id='test', source_name='Test')
    controller = LibraryController(rvdb_resolver=resolver)
    g = controller.get_games()[0]
    controller.set_favorite(g, True)
    controller.create_collection('Keep')
    controller.add_to_collection('Keep', g)
    controller.record_played(g)
    preference = 'retro-vault://overlays/retrovault/nes/classic/RetroVault_NES_Classic.cfg'
    LibraryPresentationStudioService(PresentationStore()).assign('overlay', 'game', preference, g)
    assert g.artwork == str(expected_cover)
    identity = g.local_file_id
    controller.reload_sources()
    assert controller.get_games()[0].local_file_id == identity
    code = '''
import json, sys
from controllers.library_controller import LibraryController
from services.library.rvdb_resolver import RVDBLibraryResolver
from services.presentation.store import PresentationStore
c = LibraryController(rvdb_resolver=RVDBLibraryResolver.from_bundle(sys.argv[1]))
g = c.get_games()[0]
print(json.dumps(dict(identity=g.local_file_id, game=g.rvdb_game_id, year=g.year,
    artwork=g.artwork, favorite=g.favorite, recent=c.recent(),
    collection=[x.local_file_id for x in c.collection_games('Keep')],
    overlay=PresentationStore().load()['games'][g.local_file_id].overlay)))
'''
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
    result = subprocess.run([sys.executable, '-B', '-c', code, str(tmp_path / 'bundle.json')],
                            cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == dict(identity=identity, game='game.nes', year=1991,
        artwork=str(expected_cover), favorite=True, recent=[identity], collection=[identity], overlay=preference)


def test_details_treats_metadata_as_literal_text(tmp_path):
    from PyQt6.QtWidgets import QApplication
    from ui.library.details.game_details import GameDetails
    app = QApplication.instance() or QApplication([])
    from PyQt6.QtCore import Qt
    from ui.library.widgets.game_card import GameCard
    g = game(tmp_path, title='<b>Literal title</b>', description='<b>literal description</b>', developer='<i>Studio</i>')
    details = GameDetails()
    details.show_game(g)
    assert '<b>literal description</b>' in details.description.toPlainText()
    assert '<i>Studio</i>' in details.description.toPlainText()
    card = GameCard(g)
    assert card.title.textFormat() == Qt.TextFormat.PlainText
    assert details.title.textFormat() == Qt.TextFormat.PlainText
    card.close()
    details.close()


def test_new_cover_is_found_after_refresh_and_deleted_explicit_can_return(resolver, tmp_path):
    root = tmp_path / 'covers'
    service = ArtworkService(root, resolver)
    g = game(tmp_path)
    assert service.get_artwork(g) is None
    explicit = cover(tmp_path, 'manual', 'chosen')
    g.artwork = str(explicit)
    assert service.get_artwork(g) == str(explicit)
    explicit.unlink()
    fallback = cover(root, 'NES', 'Same Game (USA)')
    service.invalidate()
    g.artwork = service.get_artwork(g) or ''
    assert g.artwork == str(fallback)
    explicit.write_bytes(b'restored')
    assert service.get_artwork(g) == str(explicit)


def test_cache_does_not_cross_canonical_platform_change(resolver, tmp_path):
    root = tmp_path / 'covers'
    nes = cover(root, 'NES', 'Same Game (USA)')
    snes = cover(root, 'SNES', 'Same Game (USA)')
    service = ArtworkService(root, resolver)
    g = game(tmp_path)
    g.artwork = service.get_artwork(g)
    assert g.artwork == str(nes)
    g.rvdb_platform_id, g.rvdb_game_id, g.platform = 'platform.snes', 'game.snes', 'SNES'
    assert service.get_artwork(g) == str(snes)
