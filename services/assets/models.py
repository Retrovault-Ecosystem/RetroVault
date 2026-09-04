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

@dataclass(frozen=True)
class AssetExecutionResult:
    moved: tuple[AssetMove, ...]

    @property
    def moved_count(self) -> int:
        return len(
            self.moved
        )

    @property
    def overlay_count(self) -> int:
        return sum(
            1
            for move in self.moved
            if move.category == "overlay"
        )

    @property
    def shader_count(self) -> int:
        return sum(
            1
            for move in self.moved
            if move.category == "shader"
        )

@dataclass(frozen=True)
class AssetPackagePlan:
    category: str
    source: Path
    destination: Path
    file_count: int
    total_bytes: int
    errors: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return (
            self.file_count > 0
            and not self.errors
        )


@dataclass(frozen=True)
class AssetPackageResult:
    category: str
    source: Path
    destination: Path
    file_count: int
    total_bytes: int

@dataclass(frozen=True)
class AssetLayoutMove:
    component: str
    source: Path
    destination: Path
    file_count: int
    total_bytes: int


@dataclass(frozen=True)
class AssetLayoutPlan:
    source_root: Path
    moves: tuple[AssetLayoutMove, ...]
    errors: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return bool(
            self.moves
        ) and not self.errors

    @property
    def file_count(self) -> int:
        return sum(
            move.file_count
            for move in self.moves
        )

    @property
    def total_bytes(self) -> int:
        return sum(
            move.total_bytes
            for move in self.moves
        )


@dataclass(frozen=True)
class AssetLayoutResult:
    moves: tuple[AssetLayoutMove, ...]

    @property
    def file_count(self) -> int:
        return sum(
            move.file_count
            for move in self.moves
        )
