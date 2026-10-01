"""Bounded, non-geometric adjustments for qualified production shaders."""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class VisualControl:
    key: str
    label: str
    parameter: str
    minimum: float
    maximum: float
    suggested: float


def controls(platform_id):
    if platform_id in ('platform.nintendo.nes', 'platform.nintendo.snes'):
        return (VisualControl('brightness', 'Brightness', 'post_br', 0.5, 3.0, 2.2 if platform_id.endswith('snes') else 1.0),
                VisualControl('mask_strength', 'Mask strength', 'maskstr', 0.0, 1.0, 0.5))
    if platform_id == 'platform.sega.genesis':
        return (VisualControl('brightness', 'Brightness', 'RVV_BRIGHTNESS', 0.5, 2.0, 1.0),
                VisualControl('mask_strength', 'Mask strength', 'RVV_MASK_STRENGTH', 0.0, 0.5, 0.0),
                VisualControl('scanline_strength', 'Scanline strength', 'RVV_SCANLINE_STRENGTH', 0.0, 0.5, 0.0))
    return ()


def validate_values(platform_id, values):
    """None means approved package behavior, not inheritance from a lower scope."""
    allowed = {c.key: c for c in controls(platform_id)}
    if not allowed or not isinstance(values, dict):
        raise ValueError('CRT adjustments require a supported production platform and mapping.')
    result = {}
    for key, value in values.items():
        if key not in allowed:
            raise ValueError(f'Unsupported CRT adjustment: {key}')
        c = allowed[key]
        if value is not None and (type(value) not in (int, float) or not isfinite(value)
                                  or not c.minimum <= value <= c.maximum):
            raise ValueError(f'{c.label} must be between {c.minimum} and {c.maximum}.')
        result[key] = value
    return result


def validate_state(data):
    if not isinstance(data, dict) or set(data) - {'systems', 'games'}:
        raise ValueError('Invalid CRT adjustment state.')
    result = {'systems': {}, 'games': {}}
    for scope in result:
        records = data.get(scope, {})
        if not isinstance(records, dict):
            raise ValueError('CRT adjustment scope must be a mapping.')
        for identity, record in records.items():
            if not isinstance(identity, str) or not identity:
                raise ValueError('CRT adjustment identity must be nonempty.')
            if scope == 'systems':
                result[scope][identity] = validate_values(identity, record)
            else:
                if not identity.startswith('local-file:') or not isinstance(record, dict) or set(record) != {'platform_id', 'values'}:
                    raise ValueError('Game CRT adjustments require a local-file identity and platform.')
                result[scope][identity] = dict(platform_id=record['platform_id'],
                    values=validate_values(record['platform_id'], record['values']))
    return result


def resolve_values(state, platform_id, game_id):
    state = validate_state(state)
    values = dict(state['systems'].get(platform_id, {}))
    game = state['games'].get(game_id)
    if game:
        if game['platform_id'] != platform_id:
            raise ValueError('Saved CRT adjustment platform does not match this edition.')
        values.update(game['values'])
    return values


def shader_parameters(platform_id, values):
    if not values:
        return {}
    values = validate_values(platform_id, values)
    return {c.parameter: str(values[c.key]) for c in controls(platform_id)
            if c.key in values and values[c.key] is not None}
