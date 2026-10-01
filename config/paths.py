"""Application resources and user roots; resolving paths never creates files."""
import os
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
RVDB_BUNDLE = APP_ROOT / 'data/rvdb/rvdb.bundle.json'


def _xdg(name, fallback):
    value = os.environ.get(name, '').strip()
    path = Path(value).expanduser() if value else None
    return path if path is not None and path.is_absolute() else Path.home() / fallback


def config_home():
    return _xdg('XDG_CONFIG_HOME', '.config')


def cache_home():
    return _xdg('XDG_CACHE_HOME', '.cache')


def data_home():
    return _xdg('XDG_DATA_HOME', '.local/share')


def config_file(name):
    return config_home() / 'retrovault' / name


def runtime_directory(name):
    return cache_home() / 'retrovault' / name
