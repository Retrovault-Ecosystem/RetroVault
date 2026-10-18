"""Master System save support must not silently activate production readiness."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from services.emulators.session import EmulatorSession
from services.library.rvdb_resolver import RVDBLibraryResolver
from services.presentation.platform_policy import PlatformPresentationPolicyRegistry, PlatformPresentationPolicyState
from services.presentation.production_package_resolver import CanonicalProductionPackageResolver
from services.saves.context import save_context
from services.saves.policy import SavePolicy
from services.saves.recovery import SaveRecovery


def test_master_system_save_roundtrip_is_separate_from_other_editions(tmp_path):
    adapters = [Mock(), Mock()]
    for adapter in adapters:
        adapter.process_running.return_value = False
    session = EmulatorSession(*adapters)
    core = tmp_path / 'genesis_plus_gx_libretro.so'
    core.write_bytes(b'controlled core fixture; never executed')
    rom = tmp_path / 'Game.sms'
    rom.write_bytes(b'controlled content fixture; never executed')
    policy = SavePolicy(tmp_path / 'managed')
    config = {'retroarch': {'cores': {'directory': str(tmp_path)}}}
    game = SimpleNamespace(local_file_id='sms-edition', rom=str(rom), core=str(core),
                           rvdb_platform_id='platform.sega.master.system')
    assert save_context(game, config, policy).states is None
    policy.enable(session, game.local_file_id, str(core), str(rom))
    other = policy.enable(session, 'other-edition', str(core), str(rom))
    context = save_context(game, config, policy)
    assert context.states != Path(other['savestate_directory'])
    state = context.states / 'Game.state'
    state.write_bytes(b'original progress')
    other_state = Path(other['savestate_directory']) / 'Game.state'
    other_state.write_bytes(b'other edition progress')
    recovery = SaveRecovery(session, tmp_path / 'backups')
    target = context.target(state, 'state')
    backup = recovery.backup(target)
    state.write_bytes(b'later progress')
    recovery.restore(target, backup)
    assert state.read_bytes() == b'original progress'
    assert other_state.read_bytes() == b'other edition progress'
    policy.disable(session, game.local_file_id, str(core), str(rom))
    assert save_context(game, config, policy).states is None
    assert state.read_bytes() == b'original progress'


def test_master_system_requires_its_own_installed_package():
    platform = 'platform.sega.master.system'
    assert PlatformPresentationPolicyRegistry.state_for(platform) is PlatformPresentationPolicyState.READY
    with pytest.raises(ValueError, match='No local presentation asset root'):
        CanonicalProductionPackageResolver.resolve(platform_id=platform, core_identity='genesis_plus_gx', config={})


def test_master_system_extension_is_unambiguous_but_sg_is_not():
    bundle = Path(__file__).resolve().parents[1] / 'data/rvdb/rvdb.bundle.json'
    resolver = RVDBLibraryResolver.from_bundle(bundle)
    assert resolver.platform_for_extension('.sms').id == 'platform.sega.master.system'
    assert resolver.platform_for_extension('.sg') is None
    assert {p.id for p in resolver.platforms_for_extension('.sg')} == {
        'platform.sega.sg1000', 'platform.sega.sc3000'}
