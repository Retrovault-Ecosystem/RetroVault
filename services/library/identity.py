"""Local file identity, independent of RVDB titles and runtime extraction paths."""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
from uuid import UUID, uuid4


def location_key(rom):
    if not rom:
        raise ValueError("Cannot persist Library state for a game without a ROM path.")
    return str(Path(rom).expanduser().resolve(strict=False))


def game_identity(game):
    identity = getattr(game, "local_file_id", "")
    return identity or location_key(getattr(game, "rom", ""))


def family_identities(game):
    """Current physical membership, never a permanent family identifier."""
    identities = [game_identity(game)]
    for variant in getattr(game, "variants", ()) or ():
        if isinstance(variant, dict) and variant.get("rom"):
            identities.append(variant.get("local_file_id") or location_key(variant["rom"]))
    return tuple(dict.fromkeys(identities))


def project_identities(games, identities):
    by_identity = {}
    for game in games:
        try:
            for identity in family_identities(game):
                by_identity[identity] = game
        except ValueError:
            continue
    result, seen = [], set()
    for identity in identities:
        game = by_identity.get(identity)
        if game is not None and id(game) not in seen:
            result.append(game)
            seen.add(id(game))
    return result


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _signature(path):
    stat = path.stat()
    return [stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns]


def _fingerprint(path, signature, control=None):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            if control is not None:
                control.report("Hashing")
            digest.update(chunk)
    if _signature(path) != signature:
        raise OSError(f"File changed while establishing identity: {path}")
    return digest.hexdigest()


def _valid_id(value):
    try:
        return isinstance(value, str) and value.startswith("local-file:") and str(UUID(value[11:])) == value[11:]
    except ValueError:
        return False


class IdentityRegistry:
    VERSION = 1

    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return {"version": self.VERSION, "files": {}, "legacy_paths": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise ValueError("Invalid Library identity registry") from exc
        if (not isinstance(data, dict) or set(data) != {"version", "files", "legacy_paths"}
                or type(data["version"]) is not int or data["version"] != self.VERSION
                or not isinstance(data["files"], dict) or not isinstance(data["legacy_paths"], dict)):
            raise ValueError("Unsupported Library identity registry")
        for identity, record in data["files"].items():
            if (not _valid_id(identity) or not isinstance(record, dict)
                    or set(record) != {"path", "platform", "signature", "sha256"}
                    or not isinstance(record["path"], str) or not Path(record["path"]).is_absolute()
                    or not isinstance(record["platform"], str)
                    or not isinstance(record["signature"], list) or len(record["signature"]) != 5
                    or not all(type(x) is int for x in record["signature"])
                    or not isinstance(record["sha256"], str) or len(record["sha256"]) != 64
                    or any(x not in "0123456789abcdef" for x in record["sha256"])):
                raise ValueError("Invalid Library identity record")
        for path, identity in data["legacy_paths"].items():
            if not Path(path).is_absolute() or not isinstance(identity, str) or identity not in data["files"]:
                raise ValueError("Invalid legacy identity mapping")
        return data

    def stage(self, games, *, control=None, original=None):
        """Assign IDs to new scan objects; do not write until the caller commits.

        A missing source never deletes records. Matching is global for this scan,
        so two new identical copies cannot race to claim one historical ID.
        """
        original = self.load() if original is None else original
        data = deepcopy(original)
        records = data["files"]
        by_path = {}
        for identity, record in records.items():
            by_path.setdefault(record["path"], []).append((identity, record))
        unique, observations = [], {}
        seen = set()
        for game in games:
            if control is not None:
                control.check()
            if not getattr(game, "rom", ""):
                unique.append(game)
                continue
            path = location_key(game.rom)
            if path in seen:
                continue
            seen.add(path)
            unique.append(game)
            try:
                signature = _signature(Path(path))
            except FileNotFoundError:
                # A vanished/unavailable file gets no newly asserted identity.
                unique.pop()
                continue
            platform = str(getattr(game, "rvdb_platform_id", "") or game.platform).casefold()
            candidates = by_path.get(path, [])
            cached = next((r for _, r in candidates if r["signature"] == signature), None)
            digest = cached["sha256"] if cached else _fingerprint(Path(path), signature, **({"control": control} if control is not None else {}))
            observations[path] = (game, platform, signature, digest)
        reserved, pending = set(), []
        for path, (game, platform, signature, digest) in observations.items():
            exact = [(i, r) for i, r in by_path.get(path, [])
                     if r["sha256"] == digest]
            if len(exact) == 1:
                identity = exact[0][0]
                reserved.add(identity)
                game.local_file_id = identity
            else:
                pending.append(path)
        by_fingerprint = defaultdict(list)
        for identity, record in records.items():
            by_fingerprint[(record["platform"], record["sha256"])].append((identity, record))
        pending_counts = Counter((observations[p][1], observations[p][3]) for p in pending)
        for path in pending:
            if control is not None:
                control.check()
            game, platform, signature, digest = observations[path]
            candidates = by_fingerprint[(platform, digest)]
            identity = None
            if len(candidates) == pending_counts[(platform, digest)] == 1:
                candidate, record = candidates[0]
                try:
                    Path(record["path"]).stat()
                except FileNotFoundError:
                    if candidate not in reserved:
                        identity = candidate
                # Other I/O errors propagate: inaccessible does not mean absent.
            identity = identity or "local-file:" + str(uuid4())
            game.local_file_id = identity
            reserved.add(identity)
        for path, (game, platform, signature, digest) in observations.items():
            records[game.local_file_id] = dict(path=path, platform=platform, signature=signature, sha256=digest)
            # Never let a replacement inherit unresolved legacy state at this path.
            data["legacy_paths"].setdefault(path, game.local_file_id)
        return unique, data

    def commit(self, data):
        if data != self.load():
            atomic_json(self.path, data)
