"""Install managed controls in an owned copy, rejecting ambiguous directives."""
import re

from config.controller_preferences import BUTTONS

# Keyboard-bound actions, not similarly named scalar configuration settings
# such as input_driver = "x". These controls are never rewritten here.
SHORTCUTS = frozenset('''toggle_fast_forward hold_fast_forward exit_emulator
reset pause_toggle frame_advance rewind hold_slowmotion toggle_slowmotion
enable_hotkey movie_record_toggle runahead_toggle preempt_toggle
save_state load_state state_slot_increase state_slot_decrease
disk_eject_toggle disk_next disk_prev screenshot mute volume_up volume_down
netplay_game_watch netplay_player_chat netplay_fade_chat shader_next shader_prev
shader_toggle cheat_index_plus cheat_index_minus cheat_toggle menu_toggle
fullscreen_toggle grab_mouse_toggle game_focus_toggle desktop_menu_toggle
overlay_next osk_toggle recording_toggle streaming_toggle ai_service
fps_toggle statistics_toggle send_debug_info close_content'''.split())


def apply_controls(text, values):
    keyboard = {value for key, value in values.items()
                if re.fullmatch(r'input_player[12]_(?:' + '|'.join(BUTTONS) + ')', key)
                and value != 'nul'}
    for key, value in re.findall(r'(?m)^\s*(input_[a-z0-9_]+)\s*=\s*"([^"\n]*)"', text):
        if key.removeprefix('input_') in SHORTCUTS and value in keyboard:
            raise ValueError(f'Controller key {value} conflicts with preserved shortcut {key}. '
                             'Choose another gameplay key.')
    allowed = {'input_autodetect_enable', 'auto_remaps_enable',
               'input_remap_binds_enable', 'input_turbo_enable',
               'input_max_users', 'input_joypad_driver',
               'input_libretro_device_p1', 'input_libretro_device_p2'}
    bindings = BUTTONS + ('l2', 'r2', 'l3', 'r3', 'l_x_plus', 'l_x_minus',
                         'l_y_plus', 'l_y_minus', 'r_x_plus', 'r_x_minus',
                         'r_y_plus', 'r_y_minus')
    for player in (1, 2):
        prefix = f'input_player{player}_'
        allowed.update(prefix + key for key in ('joypad_index', 'analog_dpad_mode'))
        allowed.update(prefix + key + suffix for key in bindings
                       for suffix in ('', '_btn', '_axis'))
    for key, value in values.items():
        if key not in allowed or not isinstance(value, str) or not re.fullmatch(r'[a-z0-9+-]+', value):
            raise ValueError('Invalid managed RetroArch control directive.')
        pattern = re.compile(rf'(?m)^[ \t]*{re.escape(key)}[ \t]*=[^\n]*$')
        matches = list(pattern.finditer(text))
        if len(matches) > 1:
            raise ValueError(f'Duplicate RetroArch control directive: {key}')
        directive = f'{key} = "{value}"'
        if matches:
            text = pattern.sub(lambda _: directive, text)
        else:
            text = text.rstrip('\n') + '\n' + directive + '\n'
    return text
