from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AssetMove:
    category: str
    source: Path
    destination: Path


@dataclass(frozen=True)
class AssetPlan:
    source_root: Path
    moves: tuple[AssetMove, ...]
    skipped: tuple[Path, ...]
    errors: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return bool(
            self.moves
        ) and not self.errors

    @property
    def overlay_count(self) -> int:
        return sum(
            1
            for move in self.moves
            if move.category == "overlay"
        )

    @property
    def shader_count(self) -> int:
        return sum(
            1
            for move in self.moves
            if move.category == "shader"
        )
