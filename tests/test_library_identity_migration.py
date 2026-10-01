import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.library.identity import IdentityRegistry, game_identity, project_identities
from services.library.identity_migration import migrate_stores
from services.library.library_service import LibraryService
from services.library.models import Game
from services.library.state import LibraryState
from services.library.collections import CollectionStore
from services.library.presentation_studio import LibraryPresentationStudioService
from services.presentation.store import PresentationStore


def make_game(path):
    return Game(Path(path).stem, "NES", 0, "", "fceumm", rom=str(path), rvdb_platform_id="platform.nintendo.nes")


def stores(root):
    return (LibraryState(root / "library-state.json"), CollectionStore(root / "collections.json"),
            PresentationStore(root / "presentation-state.json"))


def legacy(root, path):
    state, collections, presentation = stores(root)
    state.state_file.write_text(json.dumps({"favorites": [str(path)], "recent": [str(path)]}))
    collections.collections_file.write_text(json.dumps({"version": 1, "collections": [{"name": "Best", "games": [str(path)]}]}))
    presentation.presentation_file.write_text(json.dumps({"version": 1, "default": {}, "systems": {},
                                                          "games": {str(path): {"shader": "game.slangp"}}}))
    return state, collections, presentation


def test_migration_round_trip_preserves_missing_keys_and_backups(tmp_path):
    path = tmp_path / "game.nes"
    path.write_bytes(b"game")
    instances = legacy(tmp_path, path)
    missing = str(tmp_path / "absent.nes")
    state_data = json.loads(instances[0].state_file.read_text())
    state_data["favorites"].append(missing)
    instances[0].state_file.write_text(json.dumps(state_data))
    originals = {p: p.read_bytes() for p in tmp_path.glob("*.json")}
    registry = IdentityRegistry(tmp_path / "library-identities.json")
    game = make_game(path)
    _, staged = registry.stage([game])
    registry.commit(staged)
    migrate_stores(staged["legacy_paths"], *instances)
    state, collections, presentation = stores(tmp_path)
    assert state.favorites() == {game.local_file_id, missing}
    assert state.recent() == [game.local_file_id]
    assert collections.identities("Best") == [game.local_file_id]
    assert presentation.resolver().resolve(game).shader == "game.slangp"
    for path, content in originals.items():
        assert path.with_name(path.name + ".pre-identity.bak").read_bytes() == content
        assert json.loads(path.read_text())["version"] == (PresentationStore.VERSION if path == presentation.presentation_file else 2)
    after = {p: p.read_bytes() for p in tmp_path.glob("*") if p.is_file()}
    migrate_stores(staged["legacy_paths"], *stores(tmp_path))
    assert after == {p: p.read_bytes() for p in after}


def test_interrupted_migration_resumes_with_registered_id(tmp_path, monkeypatch):
    path = tmp_path / "game.nes"
    path.write_bytes(b"game")
    state, collections, presentation = legacy(tmp_path, path)
    original = collections.collections_file.read_bytes()
    registry = IdentityRegistry(tmp_path / "registry.json")
    first = make_game(path)
    _, staged = registry.stage([first])
    registry.commit(staged)
    def fail(*args):
        raise OSError("disk full")
    with monkeypatch.context() as patch:
        patch.setattr(collections, "_write", fail)
        with pytest.raises(OSError):
            migrate_stores(staged["legacy_paths"], state, collections, presentation)
    assert state.recent() == [first.local_file_id]
    assert collections.collections_file.read_bytes() == original
    second = make_game(path)
    _, staged = registry.stage([second])
    assert second.local_file_id == first.local_file_id
    migrate_stores(staged["legacy_paths"], *stores(tmp_path))
    assert collections.identities("Best") == [first.local_file_id]
    assert presentation.resolver().resolve(second).shader == "game.slangp"


def test_conflicting_overrides_are_retained_without_resurrection(tmp_path):
    path = tmp_path / "game.nes"
    path.write_bytes(b"game")
    state, collections, presentation = legacy(tmp_path, path)
    game = make_game(path)
    registry = IdentityRegistry(tmp_path / "registry.json")
    _, staged = registry.stage([game])
    registry.commit(staged)
    presentation.assign_game_shader(game.local_file_id, "new.slangp")
    migrate_stores(staged["legacy_paths"], state, collections, presentation)
    assert presentation.resolver().resolve(game).shader == "new.slangp"
    assert presentation.load()["legacy_games"][str(path)].shader == "game.slangp"
    presentation.clear_game_shader(game.local_file_id)
    migrate_stores(staged["legacy_paths"], state, collections, presentation)
    assert presentation.resolver().resolve(game).shader == ""
    assert presentation.load()["legacy_games"][str(path)].shader == "game.slangp"


@pytest.mark.parametrize("bad", ["not json", '{"version":999}', '{"favorites":[],"recent":[],"unknown":true}'])
def test_invalid_store_prevents_any_migration(tmp_path, bad):
    state, collections, presentation = legacy(tmp_path, tmp_path / "a.nes")
    state.state_file.write_text(bad)
    original = {p: p.read_bytes() for p in tmp_path.glob("*.json")}
    with pytest.raises(ValueError):
        migrate_stores({str(tmp_path / "a.nes"): "local-file:new"}, state, collections, presentation)
    assert original == {p: p.read_bytes() for p in original}
    assert not list(tmp_path.glob("*.bak"))


class Sources:
    def sources(self):
        return []


def service(root, paths):
    state, collections, presentation = stores(root)
    result = LibraryService(library_state=state, collection_store=collections, presentation_store=presentation,
                            artwork_service=SimpleNamespace(get_artwork=lambda game: None))
    result.sources = Sources()
    result.builder = SimpleNamespace(build=lambda sources: [make_game(p) for p in paths])
    return result


def test_service_state_survives_move_and_replacement_does_not_inherit(tmp_path):
    path = tmp_path / "Example (USA).nes"
    path.write_bytes(b"original")
    legacy(tmp_path, path)
    paths = [path]
    library = service(tmp_path, paths)
    first = library.load()[0]
    old_id = first.local_file_id
    paths[0] = path.rename(tmp_path / "Renamed.nes")
    assert library.reload_sources()[0] is first
    assert first.local_file_id == old_id and first.rom == str(paths[0])
    assert first.favorite
    assert library.collection_games("Best") == [first]
    assert library.presentation_store.resolver().resolve(first).shader == "game.slangp"
    paths[0].write_bytes(b"replacement")
    second = library.reload_sources()[0]
    assert second.local_file_id != old_id
    assert not second.favorite
    assert library.collection_games("Best") == []
    assert library.presentation_store.resolver().resolve(second).shader == ""
    assert old_id in library.state.favorites()


def test_hidden_edition_state_survives_preferred_edition_change(tmp_path):
    japan, usa = tmp_path / "Example (Japan).nes", tmp_path / "Example (USA).nes"
    japan.write_bytes(b"japan")
    usa.write_bytes(b"usa")
    paths = [japan]
    library = service(tmp_path, paths)
    japanese = library.load()[0]
    library.set_favorite(japanese, True)
    library.create_collection("Best")
    library.add_to_collection("Best", japanese)
    library.record_played(japanese)
    library.presentation_store.assign_game_shader(japanese.local_file_id, "japan.slangp")
    paths.append(usa)
    visible = library.reload_sources()[0]
    assert visible.rom == str(usa)
    assert visible.favorite
    assert library.collection_games("Best") == [visible]
    assert project_identities(library.games, library.recent()) == [visible]
    assert library.presentation_store.resolver().resolve(visible).shader == ""
    variant = next(v for v in visible.variants if v["rom"] == str(japan))
    edition = library._variant_game_from_record(visible, variant)
    assert edition.local_file_id == japanese.local_file_id
    assert library.presentation_store.resolver().resolve(edition).shader == "japan.slangp"
    library.set_favorite(visible, False)
    library.remove_from_collection("Best", visible)
    assert not library.state.favorites()
    assert not library.collections.identities("Best")
    assert not library.reload_sources()[0].favorite


def test_bulk_import_reconnects_move_and_replaces_content(tmp_path):
    old, moved = tmp_path / "old.nes", tmp_path / "moved.nes"
    old.write_bytes(b"original")
    library = service(tmp_path, [old])
    first = library.load()[0]
    library.set_favorite(first, True)
    old.rename(moved)
    result = library.merge_bulk_import(SimpleNamespace(games=(make_game(moved),)))
    assert result["added_count"] == 0
    assert library.games[0] is first
    assert first.rom == str(moved) and first.favorite
    moved.write_bytes(b"different")
    result = library.merge_bulk_import(SimpleNamespace(games=(make_game(moved), make_game(moved))))
    assert result["added_count"] == 1 and result["skipped_count"] == 1
    assert len(library._physical_games) == 1
    assert not library.games[0].favorite
    assert library.games[0].local_file_id != first.local_file_id


def test_reload_failure_restores_visible_and_physical_objects(tmp_path):
    path = tmp_path / "game.nes"
    path.write_bytes(b"game")
    library = service(tmp_path, [path])
    first = library.load()[0]
    physical = library._physical_games
    original = dict(vars(first))
    def fail(games):
        raise ValueError("projection failed")
    library.canonicalizer.canonicalize = fail
    with pytest.raises(ValueError):
        library.reload_sources()
    assert library.games[0] is first
    assert library._physical_games is physical
    assert vars(first) == original


def test_studio_uses_production_resolver_and_canonical_system(tmp_path):
    path = tmp_path / "game.nes"
    path.write_bytes(b"game")
    library = service(tmp_path, [path])
    game = library.load()[0]
    game.rvdb_game_id = "game.knowledge.only"
    store = library.presentation_store
    store.assign_system_overlay(game.rvdb_platform_id, "system.cfg")
    studio = LibraryPresentationStudioService(store, store.resolver)
    studio.assign_game_shader(game, "local.slangp")
    state = studio.state_for(game)
    assert state.game_id == game.local_file_id
    assert state.platform == game.rvdb_platform_id
    assert state.has_system_override
    assert state.shader == "local.slangp" and state.overlay == "system.cfg"
    assert game.rvdb_game_id not in store.load()["games"]


def test_bulk_projection_failure_preserves_existing_objects(tmp_path):
    first_path, new_path = tmp_path / "First.nes", tmp_path / "New.nes"
    first_path.write_bytes(b"first")
    new_path.write_bytes(b"new")
    library = service(tmp_path, [first_path])
    first = library.load()[0]
    before = dict(vars(first))
    physical, visible = library._physical_games, library.games
    def fail(games):
        raise ValueError("projection failed")
    library.canonicalizer.canonicalize = fail
    with pytest.raises(ValueError):
        library.merge_bulk_import(SimpleNamespace(games=(make_game(new_path),)))
    assert library.games is visible and library._physical_games is physical
    assert vars(first) == before


def test_invalid_store_does_not_commit_staged_registry(tmp_path):
    path = tmp_path / "game.nes"
    path.write_bytes(b"game")
    library = service(tmp_path, [path])
    library.collections.collections_file.write_text('{"version":999}')
    with pytest.raises(ValueError):
        library.load()
    assert not library.identity_registry.path.exists()


def test_absent_legacy_entry_migrates_when_source_returns(tmp_path):
    path = tmp_path / "game.nes"
    state, collections, presentation = legacy(tmp_path, path)
    library = service(tmp_path, [])
    assert library.load() == []
    assert state.recent() == [str(path)]
    path.write_bytes(b"returned")
    library.builder.build = lambda sources: [make_game(path)]
    game = library.reload_sources()[0]
    assert game.favorite
    assert state.recent() == [game.local_file_id]
    assert presentation.resolver().resolve(game).shader == "game.slangp"


def test_overlapping_source_paths_are_one_physical_file(tmp_path):
    path = tmp_path / "game.nes"
    path.write_bytes(b"game")
    library = service(tmp_path, [path, path])
    assert len(library.load()) == len(library._physical_games) == 1
    assert len(library.games[0].variants) == 1
