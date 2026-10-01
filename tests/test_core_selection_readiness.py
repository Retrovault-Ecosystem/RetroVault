"""Real filesystem prerequisites with process/runtime boundaries explicitly mocked."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from models.launch_profile import LaunchProfile
from services.library.core_mapper import CoreMapper
from services.presentation.platform_policy import PlatformPresentationPolicyRegistry as Policy
from services.retroarch.core_resolver import CoreResolver, core_suffix, usable_core_file
from services.retroarch.validator import LaunchValidator
from services.retroarch.diagnostics import LaunchDiagnostics
from services.retroarch.launcher import RetroArchLauncher


NES = "platform.nintendo.nes"
N64 = "platform.nintendo.n64"


def binary(root, name="fceumm", content=b"core fixture"):
    path = root / (name + "_libretro" + core_suffix())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def resolver(root):
    return CoreResolver({"retroarch": {"cores": {"directory": str(root)}}})


def files(root, core_name="fceumm"):
    executable = root / "retroarch-test"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    core = binary(root, core_name)
    rom = root / "game.nes"
    rom.write_bytes(b"ROM fixture")
    return executable, core, rom


@pytest.mark.parametrize("name", ["fceumm", "lr-fceumm", "fceumm_libretro" + core_suffix()])
def test_exact_normalized_name_resolution(tmp_path, name):
    expected = binary(tmp_path / "b")
    binary(tmp_path / "a", "fceumm_alternative")
    result = resolver(tmp_path).resolve(name, NES)
    assert result.status == "resolved" and result.path == str(expected)


def test_substring_does_not_select_foreign_core(tmp_path):
    binary(tmp_path, "snes9x2010")
    assert resolver(tmp_path).resolve("snes9x").status == "missing"


def test_distinct_installations_are_ambiguous_but_explicit_path_resolves(tmp_path):
    first, second = binary(tmp_path / "a"), binary(tmp_path / "b")
    result = resolver(tmp_path).resolve("fceumm", NES)
    assert result.status == "ambiguous"
    assert result.candidates == (str(first), str(second))
    assert resolver(tmp_path).find("fceumm") is None
    assert resolver(tmp_path).resolve(str(second), NES).path == str(second)


def test_symlink_aliases_are_one_installation(tmp_path):
    target = binary(tmp_path / "b")
    alias = tmp_path / "a" / target.name
    alias.parent.mkdir()
    alias.symlink_to(target)
    result = resolver(tmp_path).resolve("fceumm", NES)
    assert result.status == "resolved" and len(result.candidates) == 1
    assert Path(result.path).resolve() == target


@pytest.mark.parametrize("kind", ["empty", "directory", "missing", "foreign_suffix"])
def test_unusable_explicit_paths_are_rejected(tmp_path, kind):
    path = tmp_path / ("fceumm_libretro" + core_suffix())
    if kind == "empty":
        path.touch()
    elif kind == "directory":
        path.mkdir()
    elif kind == "foreign_suffix":
        path = tmp_path / "fceumm_libretro.unsupported"
        path.write_bytes(b"not native")
    assert resolver(tmp_path).resolve(str(path)).status == "unusable"
    assert not CoreResolver.contains_core(tmp_path)


def test_unreadable_core_and_unavailable_directory(tmp_path, monkeypatch):
    core = binary(tmp_path)
    monkeypatch.setattr("services.retroarch.core_resolver.os.access", lambda *args: False)
    assert not usable_core_file(core)
    assert resolver(tmp_path).resolve("fceumm").status == "unusable"
    assert not CoreResolver.contains_core(tmp_path)


def test_scan_errors_fail_closed_instead_of_selecting_partial_inventory(tmp_path, monkeypatch):
    binary(tmp_path)
    def walk(path, onerror):
        onerror(PermissionError("subdirectory unreadable"))
        yield
    monkeypatch.setattr("services.retroarch.core_resolver.os.walk", walk)
    result = resolver(tmp_path).resolve("fceumm", NES)
    assert result.status == "unusable" and "unreadable" in result.message


def test_canonical_mapper_and_selection_defaults(tmp_path):
    core = binary(tmp_path)
    assert CoreMapper().get_core(NES) == "fceumm_libretro.so"
    assert resolver(tmp_path).resolve("", NES).path == str(core)
    assert resolver(tmp_path).resolve("snes9x", NES).status == "incompatible"
    assert resolver(tmp_path).resolve("", "platform.unsupported").status == "no_policy"
    assert resolver(tmp_path).resolve("core.fceumm", NES).status == "incompatible"


def test_multiple_policy_defaults_require_selection(tmp_path, monkeypatch):
    monkeypatch.setitem(Policy.PLATFORM_CORE_COMPATIBILITY, NES, ("fceumm", "alternate"))
    core = binary(tmp_path)
    assert CoreMapper().get_core(NES) == ""
    assert resolver(tmp_path).resolve("", NES).status == "selection_required"
    assert resolver(tmp_path).resolve("fceumm", NES).path == str(core)


def test_readiness_requires_usable_files_and_resolves_path_command(tmp_path, monkeypatch):
    executable, core, rom = files(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))
    validator = LaunchValidator(executable.name, str(core))
    assert validator.validate(str(rom), platform_id=NES)["ready"]
    assert "checks still apply" in LaunchDiagnostics().explain(validator.validate(str(rom)))[0]
    executable.chmod(0o644)
    report = validator.validate(str(rom))
    assert not report["ready"] and "not executable" in report["reasons"][0]


def test_directories_cannot_pass_executable_or_core_validation(tmp_path):
    assert not LaunchValidator(str(tmp_path), str(tmp_path)).validate(str(tmp_path))["ready"]
    assert not LaunchValidator(str(tmp_path), str(tmp_path)).check_retroarch()
    assert not LaunchValidator(str(tmp_path), str(tmp_path)).check_core()


@pytest.mark.parametrize("broken", ["executable", "core", "rom", "incompatible"])
def test_direct_launcher_blocks_before_preparation_or_spawn(tmp_path, monkeypatch, broken):
    executable, core, rom = files(tmp_path)
    if broken == "executable":
        executable.chmod(0o644)
    elif broken == "core":
        core.write_bytes(b"")
    elif broken == "rom":
        rom.unlink()
    archive, primary, spawn = Mock(), Mock(), Mock()
    monkeypatch.setattr("services.retroarch.launcher.subprocess.Popen", spawn)
    launcher = RetroArchLauncher(executable=str(executable), archive_runtime=archive, primary_config_runtime=primary)
    result = launcher.launch(LaunchProfile("Test", str(rom), str(core),
                            platform_id="platform.nintendo.snes" if broken == "incompatible" else NES))
    assert not result["success"]
    archive.resolve.assert_not_called()
    primary.create.assert_not_called()
    spawn.assert_not_called()


@pytest.mark.parametrize("platform,core_name", [(N64, "mupen64plus_next"), ("platform.arcade", "mame")])
def test_installed_core_does_not_promote_unconfigured_platform(tmp_path, monkeypatch, platform, core_name):
    executable, core, rom = files(tmp_path, core_name)
    assert resolver(tmp_path).resolve(core_name, platform).status == "resolved"
    assert LaunchValidator(str(executable), str(core)).validate(str(rom), platform_id=platform)["ready"]
    archive, spawn = Mock(), Mock()
    monkeypatch.setattr("services.retroarch.launcher.subprocess.Popen", spawn)
    result = RetroArchLauncher(executable=str(executable), archive_runtime=archive).launch(
        LaunchProfile("Test", str(rom), str(core), platform_id=platform))
    assert not result["success"] and "not configured" in result["error"]
    archive.resolve.assert_not_called()
    spawn.assert_not_called()


def test_legacy_direct_launch_uses_real_file_checks(tmp_path, monkeypatch):
    executable, core, rom = files(tmp_path)
    spawn = Mock()
    spawn.return_value.poll.return_value = None
    monkeypatch.setattr("services.retroarch.launcher.subprocess.Popen", spawn)
    launcher = RetroArchLauncher(executable=str(executable),
        archive_runtime=SimpleNamespace(resolve=lambda *args, **kwargs: str(rom)),
        primary_config_runtime=SimpleNamespace(create=lambda **kwargs: None),
        session_config=SimpleNamespace(create=lambda **kwargs: ""),
        core_options_runtime=SimpleNamespace(create=lambda *args, **kwargs: ""))
    result = launcher.launch(LaunchProfile("Test", str(rom), str(core), platform_id="platform.legacy"))
    assert result["success"]
    assert spawn.call_args.args[0][:3] == [str(executable), "-L", str(core)]


def test_scanner_uses_canonical_identity_despite_display_name_change(tmp_path):
    from services.library.scanner import RomScanner
    rom = tmp_path / "Example.nes"
    rom.write_bytes(b"ROM")
    knowledge = SimpleNamespace(
        platform_for_extension=lambda extension: SimpleNamespace(id=NES, name="A new localized display name"),
        game_for_name=lambda *args: None,
    )
    games = RomScanner(rvdb_resolver=knowledge).scan(SimpleNamespace(path=str(tmp_path), name="Test"))
    assert len(games) == 1
    assert games[0].rvdb_platform_id == NES
    assert games[0].core == "fceumm_libretro.so"


@pytest.mark.parametrize("broken_settings", [False, True])
def test_details_reloads_core_directory_and_preserves_launcher_command(tmp_path, monkeypatch, broken_settings):
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from services.library.models import Game
    from ui.library.details.game_details import GameDetails
    app = QApplication.instance() or QApplication([])
    executable, _, rom = files(tmp_path)
    old_core, new_core = binary(tmp_path / "old"), binary(tmp_path / "new")
    config = {"retroarch": {"executable": str(executable), "cores": {"directory": str(old_core.parent)}}}
    monkeypatch.setattr("controllers.game_launch_controller.ConfigLoader.load", lambda self: config)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    launcher = Mock()
    launcher.command = str(executable)
    launcher.launch.return_value = {"success": True}
    played = Mock()
    details = GameDetails(launcher=launcher, played_handler=played)
    game = Game("Test", "NES", 0, "", "fceumm", rom=str(rom), rvdb_platform_id=NES,
                local_file_id="local-file:selected-edition")
    details.current_game = game
    monkeypatch.setattr(details, "_select_cheats", lambda *args, **kwargs: [])
    config["retroarch"]["cores"]["directory"] = str(new_core.parent)
    config["retroarch"]["executable"] = "/not/the/active/launcher"
    if broken_settings:
        def fail(self):
            raise ValueError("invalid settings")
        monkeypatch.setattr("controllers.game_launch_controller.ConfigLoader.load", fail)
    details.launch_game()
    if broken_settings:
        launcher.launch.assert_not_called()
        played.assert_not_called()
        assert "Unable to load core settings" in details.launch_status.text()
    else:
        launcher.launch.assert_called_once()
        assert launcher.launch.call_args.args[0].core == str(new_core)
        assert launcher.command == str(executable)
        assert played.call_args.args[0].local_file_id == game.local_file_id
    details.close()


def test_ready_package_gate_still_runs_after_valid_prerequisites(tmp_path, monkeypatch):
    executable, core, rom = files(tmp_path)
    spawn, archive = Mock(), Mock()
    def invalid_package(**kwargs):
        raise ValueError("qualified package asset is missing")
    monkeypatch.setattr("services.retroarch.launcher.CanonicalProductionPackageResolver.resolve", invalid_package)
    monkeypatch.setattr("services.retroarch.launcher.subprocess.Popen", spawn)
    result = RetroArchLauncher(executable=str(executable), archive_runtime=archive).launch(
        LaunchProfile("Test", str(rom), str(core), platform_id=NES))
    assert result == {"success": False, "error": "qualified package asset is missing"}
    archive.resolve.assert_not_called()
    spawn.assert_not_called()


def test_core_file_does_not_require_executable_permission(tmp_path):
    core = binary(tmp_path)
    core.chmod(0o644)
    assert usable_core_file(core)
    assert CoreResolver.contains_core(tmp_path)


def test_rom_readability_is_required(tmp_path, monkeypatch):
    executable, core, rom = files(tmp_path)
    monkeypatch.setattr("services.retroarch.validator.os.access", lambda *args: False)
    assert not LaunchValidator(str(executable), str(core)).check_rom(str(rom))


def test_explicit_relative_command_keeps_its_path_semantics(tmp_path, monkeypatch):
    executable, core, rom = files(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", "/nonexistent")
    launcher = RetroArchLauncher(executable=" ./retroarch-test ")
    assert launcher.command == "./retroarch-test"
    assert LaunchValidator(launcher.command, str(core)).validate(str(rom))["ready"]


def test_malformed_core_directory_has_structured_failure():
    result = CoreResolver({"retroarch": {"cores": {"directory": 123}}}).resolve("fceumm")
    assert result.status == "unusable"
