from copy import deepcopy
import pytest
from config.controller_preferences import defaults, validate_preferences, DEFAULT_KEYS
from services.input.assignments import resolve_players


def device(serial='unit1',instance=3):
    return dict(guid='test',serial=serial,name='Pad',session='session',instance=instance,index=0,buttons=12,axes=2)


def player(d):
    return dict(kind='gamepad',device={k:d[k] for k in ('guid','serial','name','session','instance')},bindings={k:'b0' for k in DEFAULT_KEYS})


def test_defaults_do_not_assign_or_modify_controls():
    assert all(p['mode']=='existing' for p in validate_preferences(defaults()).values())
    assert resolve_players(defaults()['retroarch'],[])==()


def test_serial_recovers_assignment_but_ambiguous_pair_does_not():
    d=device();p=dict(mode='managed',players=[player(d)])
    changed={**d,'instance':6,'index':1,'session':'new'}
    assert resolve_players(p,[changed])[0][1]['index']==1
    with pytest.raises(ValueError):resolve_players(p,[d,changed])
    with pytest.raises(ValueError):resolve_players(p,[])
    assert p['players'][0]['device']['instance']==3


def test_no_serial_requires_reselection_after_reconnect():
    d=device('');p=dict(mode='managed',players=[player(d)])
    assert resolve_players(p,[d])
    with pytest.raises(ValueError):resolve_players(p,[{**d,'instance':4}])
    with pytest.raises(ValueError):resolve_players(p,[{**d,'session':'new'}])


def test_duplicate_player_device_rejected():
    d=device();p=dict(mode='managed',players=[player(d),player(d)])
    with pytest.raises(ValueError):resolve_players(p,[d])


@pytest.mark.parametrize('bad',['F1','x\nvideo_driver=x','Ctrl+x','"','b-1','a0:up'])
def test_invalid_keyboard_binding_rejected(bad):
    value=defaults();value['retroarch']=dict(mode='managed',players=[dict(kind='keyboard',device={},bindings={**DEFAULT_KEYS,'a':bad})])
    with pytest.raises(ValueError):validate_preferences(value)
