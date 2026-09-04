from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ShaderPreset:
    name: str
    preset_path: Path
    relative_preset: Path
    preset_type: str
    shader_paths: tuple[Path, ...]
    missing_shaders: tuple[Path, ...]

    @property
    def ready(self) -> bool:
        return not self.missing_shaders

    @property
    def shader_count(self) -> int:
        return len(
            self.shader_paths
        )
