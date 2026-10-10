from pathlib import Path

SUPPORTED_ARTWORK_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class ArtworkService:
    """Resolve local Library covers, independently of runtime presentation assets."""

    def __init__(self, directory=None, rvdb_resolver=None, control=None):
        self.control = control
        self.rvdb_resolver = rvdb_resolver
        self.set_directory(directory)

    def set_directory(self, directory):
        self.directory = Path(directory).expanduser() if directory else None
        self.invalidate()

    def invalidate(self):
        self.cache = {}
        self._index = None

    @staticmethod
    def _identity(game):
        location = (getattr(game, "rom", "") or
                    (getattr(game, "name", ""), getattr(game, "platform", "")))
        return (location, getattr(game, "rvdb_platform_id", ""),
                getattr(game, "rvdb_game_id", ""))

    def _build_index(self):
        if self._index is not None:
            return self._index
        index = {}
        if self.directory is not None and self.directory.is_dir():
            try:
                for path in self.directory.rglob("*"):
                    if self.control is not None:
                        self.control.check()
                    if path.is_file() and path.suffix.lower() in SUPPORTED_ARTWORK_EXTENSIONS:
                        index.setdefault(path.stem.casefold(), []).append(path)
            except OSError:
                index = {}
        self._index = index
        return index

    def _select(self, paths, game):
        platform_id = getattr(game, "rvdb_platform_id", "")
        platform_name = str(getattr(game, "platform", "") or "").strip().casefold()
        own_names = {platform_name} - {"", "unknown"}
        recognized = {}
        if self.rvdb_resolver is not None:
            for platform in self.rvdb_resolver.platforms():
                for name in (platform.id, platform.name, *platform.aliases):
                    recognized.setdefault(name.casefold(), set()).add(platform.id)
                if platform.id == platform_id:
                    own_names.update(n.casefold() for n in (platform.id, platform.name, *platform.aliases))
        scoped, unscoped = [], []
        for path in paths:
            if not path.is_file():
                continue
            parts = {part.casefold() for part in path.relative_to(self.directory).parts[:-1]}
            scopes = set().union(*(recognized.get(part, set()) for part in parts))
            if scopes and (not platform_id or scopes != {platform_id}):
                continue
            if parts & own_names:
                scoped.append(path)
            else:
                unscoped.append(path)
        candidates = scoped or unscoped
        return str(candidates[0]) if len(candidates) == 1 else None

    def _discover_artwork(self, game):
        rom = getattr(game, "rom", "")
        if not rom:
            return None
        index = self._build_index()
        matches = index.get(Path(rom).stem.casefold(), [])
        if matches:
            # Ambiguous exact matches must not silently fall through to another title.
            return self._select(matches, game)
        game_id = getattr(game, "rvdb_game_id", "")
        if game_id and self.rvdb_resolver is not None:
            canonical = self.rvdb_resolver.service.game(game_id)
            if canonical and getattr(game, "rvdb_platform_id", "") in canonical.platforms:
                return self._select(index.get(canonical.name.casefold(), []), game)
        return None

    def get_artwork(self, game):
        identity = self._identity(game)
        current = getattr(game, "artwork", "")
        origin = getattr(game, "artwork_origin", "")
        explicit = getattr(game, "artwork_explicit", "")
        if current and origin != "discovered":
            explicit = current
        if explicit:
            game.artwork_explicit = explicit
            path = Path(explicit).expanduser()
            if path.is_file():
                game.artwork_origin = "explicit"
                self.cache[identity] = str(path)
                return str(path)
        cached = self.cache.get(identity)
        if cached and Path(cached).is_file():
            game.artwork_origin = "discovered"
            return cached
        self.cache.pop(identity, None)
        discovered = self._discover_artwork(game)
        game.artwork_origin = "discovered" if discovered else ""
        if discovered:
            self.cache[identity] = discovered
        return discovered
