from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Overlay:
    name: str
    config_path: Path
    relative_config: Path
    image_paths: tuple[Path, ...]
    missing_images: tuple[Path, ...]

    @property
    def ready(self) -> bool:
        return not self.missing_images

    @property
    def image_count(self) -> int:
        return len(
            self.image_paths
        )
