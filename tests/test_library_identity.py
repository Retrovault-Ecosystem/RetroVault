from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.library.identity import IdentityRegistry, game_identity, location_key
from services.library.models import Game


def game(path, platform="platform.nintendo.nes"):
    return Game(Path(path).stem, "NES", 0, "", "fceumm", rom=str(path), rvdb_platform_id=platform)


def register(registry, *games):
    result, staged = registry.stage(games)
    registry.commit(staged)
    return result


def test_rename_restart_and_hash_cache(tmp_path, monkeypatch):
    path = tmp_path / "original.nes"
    path.write_bytes(b"original")
    registry = IdentityRegistry(tmp_path / "registry.json")
    first = register(registry, game(path))[0]
    moved = path.rename(tmp_path / "renamed.nes")
    second = register(IdentityRegistry(registry.path), game(moved))[0]
    assert game_identity(first) == game_identity(second)
    assert registry.load()["legacy_paths"][str(path)] == first.local_file_id
    monkeypatch.setattr("services.library.identity._fingerprint", lambda *args: pytest.fail("unchanged file rehashed"))
    assert register(registry, game(moved))[0].local_file_id == first.local_file_id


def test_replacement_does_not_inherit_identity_or_legacy_binding(tmp_path):
    path = tmp_path / "game.nes"
    path.write_bytes(b"first")
    registry = IdentityRegistry(tmp_path / "registry.json")
    first = register(registry, game(path))[0]
    path.write_bytes(b"replacement")
    second = register(registry, game(path))[0]
    assert first.local_file_id != second.local_file_id
    assert registry.load()["legacy_paths"][str(path)] == first.local_file_id


def test_copies_are_separate_and_ambiguous_moves_do_not_merge(tmp_path):
    paths = [tmp_path / f"{i}.nes" for i in range(4)]
    for path in paths[:2]:
        path.write_bytes(b"same")
    registry = IdentityRegistry(tmp_path / "registry.json")
    first, second = register(registry, *(game(p) for p in paths[:2]))
    assert first.local_file_id != second.local_file_id
    for old, new in zip(paths[:2], paths[2:]):
        old.rename(new)
    third, fourth = register(registry, *(game(p) for p in paths[2:]))
    assert len({g.local_file_id for g in (first, second, third, fourth)}) == 4


def test_two_new_copies_cannot_claim_one_missing_file(tmp_path):
    old = tmp_path / "old.nes"
    old.write_bytes(b"same")
    registry = IdentityRegistry(tmp_path / "registry.json")
    first = register(registry, game(old))[0]
    old.unlink()
    a, b = tmp_path / "a.nes", tmp_path / "b.nes"
    a.write_bytes(b"same")
    b.write_bytes(b"same")
    copies = register(registry, game(a), game(b))
    assert len({first.local_file_id, *(g.local_file_id for g in copies)}) == 3


def test_coexisting_copy_and_platform_mismatch_do_not_reconnect(tmp_path):
    a, b, c = (tmp_path / name for name in ("a.nes", "b.nes", "c.sfc"))
    a.write_bytes(b"same")
    b.write_bytes(b"same")
    registry = IdentityRegistry(tmp_path / "registry.json")
    first = register(registry, game(a))[0]
    second = register(registry, game(b))[0]
    a.rename(c)
    third = register(registry, game(c, "platform.nintendo.snes"))[0]
    assert len({g.local_file_id for g in (first, second, third)}) == 3


def test_overlap_symlink_and_unavailable_source(tmp_path):
    a = tmp_path / "a.nes"
    a.write_bytes(b"same")
    alias = tmp_path / "alias.nes"
    alias.symlink_to(a)
    registry = IdentityRegistry(tmp_path / "registry.json")
    assert len(register(registry, game(a), game(alias), game(a))) == 1
    original = registry.path.read_bytes()
    register(registry)
    assert registry.path.read_bytes() == original
    a.unlink()
    register(registry, game(a))
    assert registry.path.read_bytes() == original


def test_hashing_failure_does_not_commit(tmp_path, monkeypatch):
    a = tmp_path / "a.nes"
    a.write_bytes(b"same")
    registry = IdentityRegistry(tmp_path / "registry.json")
    def fail(*args):
        raise PermissionError("unreadable")
    monkeypatch.setattr("services.library.identity._fingerprint", fail)
    with pytest.raises(PermissionError):
        register(registry, game(a))
    assert not registry.path.exists()


def test_changing_file_is_not_registered(tmp_path, monkeypatch):
    from services.library import identity
    a = tmp_path / "a.nes"
    a.write_bytes(b"same")
    original = identity._signature
    calls = []
    def changing(path):
        result = original(path)
        calls.append(1)
        if len(calls) > 1:
            result[-1] += 1
        return result
    monkeypatch.setattr(identity, "_signature", changing)
    registry = IdentityRegistry(tmp_path / "registry.json")
    with pytest.raises(OSError, match="changed"):
        register(registry, game(a))
    assert not registry.path.exists()


@pytest.mark.parametrize("payload", [[], {}, {"version": 9, "files": {}, "legacy_paths": {}},
    {"version": 1, "files": {"bad": {}}, "legacy_paths": {}},
    {"version": 1, "files": {}, "legacy_paths": {"/bad": "missing"}}])
def test_invalid_registry_is_preserved(tmp_path, payload):
    registry = IdentityRegistry(tmp_path / "registry.json")
    registry.path.write_text(json.dumps(payload))
    original = registry.path.read_bytes()
    with pytest.raises(ValueError):
        registry.stage([])
    assert registry.path.read_bytes() == original


def test_registry_failed_replace_leaves_original(tmp_path, monkeypatch):
    from services.library import identity
    a = tmp_path / "a.nes"
    a.write_bytes(b"same")
    registry = IdentityRegistry(tmp_path / "registry.json")
    register(registry, game(a))
    original = registry.path.read_bytes()
    a.write_bytes(b"changed")
    _, staged = registry.stage([game(a)])
    def fail(*args):
        raise OSError("disk")
    monkeypatch.setattr(identity.os, "replace", fail)
    with pytest.raises(OSError):
        registry.commit(staged)
    assert registry.path.read_bytes() == original
    assert not list(tmp_path.glob("*.tmp"))


def test_later_rvdb_enrichment_does_not_change_local_identity(tmp_path):
    path = tmp_path / "game.nes"
    path.write_bytes(b"game")
    registry = IdentityRegistry(tmp_path / "registry.json")
    first = register(registry, game(path, ""))[0]
    enriched = register(registry, game(path))[0]
    assert first.local_file_id == enriched.local_file_id
