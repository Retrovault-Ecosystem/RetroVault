"""Opt-in, backend-specific controls with strict save/launch validation."""
from copy import deepcopy
import re

BUTTONS = ('up', 'down', 'left', 'right', 'start', 'select', 'a', 'b', 'x', 'y', 'l', 'r')
KEYS = ('up','down','left','right','return','tab','space') + tuple('abcdefghijklmnopqrstuvwxyz')
DEFAULT_KEYS = dict(zip(BUTTONS, ('up','down','left','right','return','tab','x','z','s','a','q','w')))


def defaults():
    return {backend: {'mode': 'existing', 'players': []} for backend in ('retroarch','snes9x')}


def validate_preferences(value):
    if not isinstance(value, dict) or set(value) != {'retroarch', 'snes9x'}:
        raise ValueError('Controller settings must specify RetroArch and Snes9x profiles.')
    for backend, profile in value.items():
        if not isinstance(profile, dict) or set(profile) != {'mode','players'}:
            raise ValueError(f'Invalid {backend} controller profile.')
        if profile['mode'] not in ('existing','managed') or not isinstance(profile['players'], list):
            raise ValueError('Invalid controller mode or player list.')
        players = profile['players']
        if len(players) > 2 or (profile['mode'] == 'managed' and not players):
            raise ValueError('Managed profiles require one or two players.')
        for index, player in enumerate(players):
            if not isinstance(player, dict) or set(player) != {'kind','device','bindings'}:
                raise ValueError('Invalid player assignment.')
            if player['kind'] not in ('keyboard','gamepad'):
                raise ValueError('Choose keyboard or gamepad.')
            if player['kind'] == 'keyboard' and index != 0:
                raise ValueError('Keyboard is limited to Player 1 in this qualification slice.')
            bindings = player['bindings']
            if not isinstance(bindings, dict) or set(bindings) != set(BUTTONS):
                raise ValueError('Map all twelve standard controls.')
            for binding in bindings.values():
                if not isinstance(binding,str):
                    raise ValueError('Bindings must be text.')
                if player['kind']=='keyboard':
                    if binding not in KEYS:
                        raise ValueError('Unsupported keyboard binding; shortcuts are not remapped.')
                elif not re.fullmatch(r'(?:b(?:0|[1-9][0-9]{0,2})|a(?:0|[1-9][0-9]?):[+-])',binding):
                    raise ValueError('Use b0 for button 0 or a0:+ / a0:- for an axis direction.')
            device=player['device']
            if not isinstance(device,dict) or set(device)-{'guid','serial','name','session','instance'}:
                raise ValueError('Invalid controller identity.')
            if player['kind']=='gamepad':
                if not all(isinstance(device.get(k),str) for k in ('guid','serial','name','session')) or type(device.get('instance')) is not int:
                    raise ValueError('Select a discovered controller.')
                if not device['guid']:
                    raise ValueError('Controller identification unavailable.')
    return deepcopy(value)


def from_config(config):
    return validate_preferences(config.get('controllers', defaults()))
