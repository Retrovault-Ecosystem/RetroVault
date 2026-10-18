"""Read-only save context for one already-selected Library edition."""
from dataclasses import dataclass
import hashlib
from pathlib import Path

from config.paths import data_home
from services.emulators.models import selected_backend, executable_path, SNES9X
from services.retroarch.core_resolver import CoreResolver
from services.saves.policy import SavePolicy
from services.saves.recovery import SaveTarget


@dataclass(frozen=True)
class SaveContext:
    local_file_id: str
    rom: Path
    backend: str
    core: str
    runtime: Path
    sram: Path | None
    states: Path | None

    def target(self, path, kind):
        root = self.sram if kind == 'sram' else self.states if kind == 'state' else None
        path = Path(path).absolute()
        if root is None or path.parent != root.absolute():
            raise ValueError('Select an existing save from the displayed destination.')
        return SaveTarget(path, self.local_file_id, self.backend, self.core, kind,
                          hashlib.sha256(self.runtime.read_bytes()).hexdigest(),
                          hashlib.sha256(self.rom.read_bytes()).hexdigest())


def save_context(game, config, policy=None):
    identity = getattr(game, 'local_file_id', '') or ''
    if not identity:
        raise ValueError('Save management requires a registered physical edition.')
    rom = Path(game.rom).expanduser().absolute()
    if rom.suffix.lower() not in ('.nes', '.sfc', '.smc', '.md', '.gen', '.bin') or not rom.is_file():
        raise ValueError('Save management currently requires an existing loose cartridge file.')
    backend = selected_backend(config, getattr(game, 'rvdb_platform_id', ''))
    if backend == SNES9X:
        runtime = Path(executable_path(config.get('emulation', {}).get('snes9x_executable', '')))
        root = data_home() / 'retrovault/emulators/snes9x' / hashlib.sha256(identity.encode()).hexdigest()
        return SaveContext(identity, rom, backend, 'snes9x', runtime, root / 'sram', root / 'states')
    resolution = CoreResolver(config).resolve(game.core, platform_id=getattr(game, 'rvdb_platform_id', ''))
    if not resolution.path:
        raise ValueError(resolution.message)
    runtime = Path(resolution.path)
    values = (policy or SavePolicy()).settings(identity, str(runtime), str(rom))
    return SaveContext(identity, rom, backend, str(runtime), runtime,
                       Path(values['savefile_directory']) if values else None,
                       Path(values['savestate_directory']) if values else None)
