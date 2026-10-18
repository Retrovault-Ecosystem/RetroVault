"""Translate only validated, opt-in controller profiles at the launch boundary."""
from config.controller_preferences import from_config, BUTTONS
from .assignments import resolve_players
from .devices import inventory


def resolved_profile(config, backend, devices=None):
    profile=from_config(config)[backend]
    if profile['mode']=='existing':
        return None
    if devices is None:
        devices=inventory.snapshot() if any(p['kind']=='gamepad' for p in profile['players']) else []
    players=resolve_players(profile,devices)
    for player,device in players:
        if device:
            # Native Snes9x encodes a one-based device in four bits.
            # RetroArch supports sixteen SDL slots. Reject overflow, never wrap.
            limit = 15 if backend == 'snes9x' else 16
            if type(device['index']) is not int or not 0 <= device['index'] < limit:
                raise ValueError('Assigned controller exceeds the backend device limit.')
            for binding in player['bindings'].values():
                number=int(binding[1:].split(':')[0])
                maximum=device['buttons'] if binding[0]=='b' else device['axes']
                if backend == 'retroarch' and device.get('standardized'):
                    # SDL2 GameController's original standard button/axis set;
                    # newer auxiliary controls are outside this bounded slice.
                    maximum = 15 if binding[0] == 'b' else 6
                if backend == 'snes9x' and binding[0] == 'b':
                    maximum = min(maximum, 512)
                if not 0<=number<maximum:
                    raise ValueError('Mapping exceeds the assigned controller button/axis count.')
    return players


def retroarch_values(config, devices=None):
    players=resolved_profile(config,'retroarch',devices)
    if players is None:
        return {}
    values={'input_autodetect_enable': 'false',
            'auto_remaps_enable': 'false',
            'input_remap_binds_enable': 'false',
            'input_turbo_enable': 'false', 'input_max_users': '2'}
    if any(device for _,device in players):
        # Opt-in managed gamepads use one explicitly supported enumeration driver.
        values['input_joypad_driver']='sdl2'
    for index in range(2):
        prefix=f'input_player{index+1}_'
        player,device=players[index] if index<len(players) else (None,None)
        values[f'input_libretro_device_p{index + 1}'] = '1' if player else '0'
        # This directive is an integer, not a key binding. With autoconfig
        # disabled and every pad binding cleared, a keyboard needs no invalid
        # or out-of-bounds sentinel device index.
        values[prefix+'joypad_index']=str(device['index']) if device else '0'
        values[prefix+'analog_dpad_mode']='0'
        auxiliary = ('l2', 'r2', 'l3', 'r3', 'l_x_plus', 'l_x_minus',
                     'l_y_plus', 'l_y_minus', 'r_x_plus', 'r_x_minus',
                     'r_y_plus', 'r_y_minus')
        for button in BUTTONS + auxiliary:
            values[prefix+button]='nul'
            values[prefix+button+'_btn']='nul'
            values[prefix+button+'_axis']='nul'
            if player and button in BUTTONS:
                binding=player['bindings'][button]
                if not device:
                    values[prefix+button]='enter' if binding == 'return' else binding
                elif binding.startswith('b'):
                    values[prefix+button+'_btn']=binding[1:]
                else:
                    axis,direction=binding[1:].split(':')
                    values[prefix+button+'_axis']=direction+axis
    return values


def snes9x_sections(config, devices=None):
    players=resolved_profile(config,'snes9x',devices)
    if players is None:
        return {}
    sections={'Input': {'ControllerPort0': 'joypad',
                       'ControllerPort1': 'joypad' if len(players) > 1 else 'none'}}
    names={'up':'Up','down':'Down','left':'Left','right':'Right','start':'Start','select':'Select'}
    keys={'up':'Up','down':'Down','left':'Left','right':'Right','return':'Return','tab':'Tab'}
    # Snes9x GTK has alternate banks for the same player ports. Clear those
    # only in the managed copy so an old alternate mapping cannot also fire.
    for index in (0, 1, 5, 6):
        player,device=players[index] if index<len(players) else (None,None)
        values={}
        for modifier in ('Turbo', 'Sticky'):
            for button in ('A', 'B', 'X', 'Y', 'L', 'R'):
                values[f'{modifier} {button}'] = 'Unset'
        for button in BUTTONS:
            value='Unset'
            if player:
                binding=player['bindings'][button]
                if not device:
                    value='Keyboard '+keys.get(binding,binding)
                elif binding.startswith('b'):
                    value=f'Joystick {device["index"]+1} Button {binding[1:]}'
                else:
                    axis,direction=binding[1:].split(':')
                    value=f'Joystick {device["index"]+1} Axis {axis} {direction} 50%'
            values[names.get(button,button.upper())]=value
        sections[f'Joypad {index}']=values
    return sections
