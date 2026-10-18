from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from services.input.devices import DeviceInventory


def library():
    return SimpleNamespace(
        SDL_JoystickUpdate=Mock(), SDL_NumJoysticks=lambda: 1,
        SDL_JoystickOpen=lambda _: 123, SDL_JoystickClose=Mock(),
        SDL_JoystickGetSerial=lambda _: b'serial',
        SDL_JoystickGetDeviceInstanceID=lambda _: 8,
        SDL_JoystickGetDeviceGUID=lambda _: SimpleNamespace(data=bytes(range(16))),
        SDL_JoystickNameForIndex=lambda _: b'Example pad',
        SDL_JoystickNumButtons=lambda _: 12, SDL_JoystickNumAxes=lambda _: 4,
        SDL_IsGameController=lambda _: 1)


def test_snapshot_keeps_identity_separate_from_index_and_closes_handle():
    inventory = DeviceInventory()
    inventory.lib = library()
    device, = inventory.snapshot()
    assert device['index'] == 0 and device['instance'] == 8
    assert device['serial'] == 'serial' and device['standardized']
    assert device['session'] == inventory.session
    inventory.lib.SDL_JoystickClose.assert_called_once_with(123)


def test_enumeration_error_still_closes_open_handle():
    inventory = DeviceInventory()
    inventory.lib = library()
    def fail(_):
        raise OSError('disconnected')
    inventory.lib.SDL_JoystickNumButtons = fail
    with pytest.raises(OSError):
        inventory.snapshot()
    inventory.lib.SDL_JoystickClose.assert_called_once_with(123)


def test_missing_optional_serial_requires_session_identity():
    inventory = DeviceInventory()
    inventory.lib = library()
    del inventory.lib.SDL_JoystickGetSerial
    assert inventory.snapshot()[0]['serial'] == ''


def test_missing_sdl_is_actionable(monkeypatch):
    monkeypatch.setattr('services.input.devices.find_library', lambda _: None)
    with pytest.raises(ValueError, match='existing emulator controls'):
        DeviceInventory().snapshot()
