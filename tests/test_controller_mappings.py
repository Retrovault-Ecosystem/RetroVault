"""Backend namespaces and inactive bindings are not interchangeable."""
import pytest

from config.controller_preferences import DEFAULT_KEYS, defaults
from services.input.mappings import retroarch_values, snes9x_sections


def preferences(kind='keyboard', *, standardized=False, binding='b0'):
    device = dict(guid='guid', serial='serial', name='pad', session='session', instance=7)
    player = dict(kind=kind, device=device if kind == 'gamepad' else {},
                  bindings=dict(DEFAULT_KEYS) if kind == 'keyboard' else
                  {key: binding for key in DEFAULT_KEYS})
    value = defaults()
    for backend in value:
        value[backend] = dict(mode='managed', players=[player])
    return {'controllers': value}, [{**device, 'index': 1, 'buttons': 2, 'axes': 2,
                                   'standardized': standardized}]


def test_existing_mode_emits_no_overrides():
    assert retroarch_values({}) == {}
    assert snes9x_sections({}) == {}


def test_keyboard_clears_inherited_pad_and_analog_bindings():
    config, _ = preferences()
    values = retroarch_values(config)
    assert values['input_player1_a'] == 'x'
    assert values['input_player1_a_btn'] == 'nul'
    assert values['input_player1_joypad_index'] == '0'
    assert values['input_player2_a'] == 'nul'
    assert values['input_player2_l_x_plus_axis'] == 'nul'
    assert values['input_autodetect_enable'] == 'false'
    assert values['input_remap_binds_enable'] == 'false'


def test_standardized_retroarch_numbers_are_not_native_raw_numbers():
    config, devices = preferences('gamepad', standardized=True, binding='b14')
    assert retroarch_values(config, devices)['input_player1_a_btn'] == '14'
    with pytest.raises(ValueError, match='count'):
        snes9x_sections(config, devices)


def test_native_one_based_device_and_axis_syntax():
    config, devices = preferences('gamepad', binding='a1:-')
    assert snes9x_sections(config, devices)['Joypad 0']['A'] == 'Joystick 2 Axis 1 - 50%'
    assert retroarch_values(config, devices)['input_player1_a_axis'] == '-1'


def test_native_clears_alternate_and_turbo_bindings():
    config, _ = preferences()
    values = snes9x_sections(config)
    assert values['Joypad 0']['Start'] == 'Keyboard Return'
    assert values['Joypad 0']['Turbo A'] == 'Unset'
    for section in ('Joypad 1', 'Joypad 5', 'Joypad 6'):
        assert set(values[section].values()) == {'Unset'}


@pytest.mark.parametrize('translate,index', [(retroarch_values, 16), (snes9x_sections, 15)])
def test_overflowing_device_index_fails_closed(translate, index):
    config, devices = preferences('gamepad')
    devices[0]['index'] = index
    with pytest.raises(ValueError, match='device limit'):
        translate(config, devices)


def test_existing_retroarch_shortcut_conflict_is_reported_without_rebinding():
    from services.input.retroarch_config import apply_controls
    text = 'input_exit_emulator = "x"\n'
    config, _ = preferences()
    with pytest.raises(ValueError, match='preserved shortcut'):
        apply_controls(text, retroarch_values(config))


def test_x_input_driver_is_not_a_keyboard_shortcut():
    from services.input.retroarch_config import apply_controls
    config, _ = preferences()
    assert 'input_driver = "x"' in apply_controls('input_driver = "x"\n', retroarch_values(config))


def test_start_key_uses_each_backends_actual_keyboard_vocabulary():
    # RetroArch v1.22.2 input_config_key_map spells RETROK_RETURN "enter";
    # Snes9x GTK parses the GDK key name "Return". Shared preferences must
    # never be copied verbatim into both backend configuration formats.
    config, _ = preferences()
    assert retroarch_values(config)['input_player1_start'] == 'enter'
    assert snes9x_sections(config)['Joypad 0']['Start'] == 'Keyboard Return'
    assert config['controllers']['retroarch']['players'][0]['bindings']['start'] == 'return'


def test_translated_enter_still_checks_preserved_exit_shortcut():
    from services.input.retroarch_config import apply_controls
    config, _ = preferences()
    with pytest.raises(ValueError, match='preserved shortcut input_exit_emulator'):
        apply_controls('input_exit_emulator = "enter"\n', retroarch_values(config))
