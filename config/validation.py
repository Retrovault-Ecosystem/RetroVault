"""Validate known configuration fields without inspecting installations or writing."""
from pathlib import Path


def validate_config(data):
    def mapping(value, field):
        if not isinstance(value, dict):
            raise ValueError(f'{field} must be a mapping.')
        return value

    def string(value, field, *, path=False):
        if not isinstance(value, str):
            raise ValueError(f'{field} must be a string.')
        if path and value and not Path(value).expanduser().is_absolute():
            raise ValueError(f'{field} must be an absolute path or begin with ~.')

    mapping(data, 'Configuration')
    if 'retroarch' in data:
        section = mapping(data['retroarch'], 'retroarch')
        for key in ('executable', 'primary_config'):
            if key in section:
                string(section[key], f'retroarch.{key}', path=key == 'primary_config')
        executable = section.get('executable', '')
        if '/' in executable:
            string(executable, 'retroarch.executable', path=True)
        if 'cores' in section:
            cores = mapping(section['cores'], 'retroarch.cores')
            if 'directory' in cores:
                string(cores['directory'], 'retroarch.cores.directory', path=True)
    if 'paths' in data:
        for key in ('overlays', 'shaders', 'artwork'):
            paths = mapping(data['paths'], 'paths')
            if key in paths:
                entry = mapping(paths[key], f'paths.{key}')
                if 'directory' in entry:
                    string(entry['directory'], f'paths.{key}.directory', path=True)
    if 'library' in data:
        section = mapping(data['library'], 'library')
        if 'sources' in section:
            sources = section['sources']
            if not isinstance(sources, list):
                raise ValueError('library.sources must be a list.')
            identities = set()
            for index, source in enumerate(sources):
                field = f'library.sources[{index}]'
                mapping(source, field)
                for key in ('id', 'name', 'type', 'path'):
                    string(source.get(key), f'{field}.{key}', path=key == 'path')
                    if not source[key].strip():
                        raise ValueError(f'{field}.{key} cannot be empty.')
                if source['type'] != 'local':
                    raise ValueError(f'{field}.type must be local.')
                if type(source.get('enabled')) is not bool:
                    raise ValueError(f'{field}.enabled must be a boolean.')
                if source['id'] in identities:
                    raise ValueError(f'{field}.id duplicates {source["id"]}.')
                identities.add(source['id'])
    if 'emulation' in data:
        section = mapping(data['emulation'], 'emulation')
        backend = section.get('snes_backend', 'retroarch')
        if backend not in ('retroarch', 'snes9x'):
            raise ValueError('emulation.snes_backend must be retroarch or snes9x.')
        if 'snes9x_executable' in section:
            value = section['snes9x_executable']
            string(value, 'emulation.snes9x_executable')
            if '/' in value:
                string(value, 'emulation.snes9x_executable', path=True)
    return data
