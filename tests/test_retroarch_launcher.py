from unittest.mock import patch

from models.launch_profile import (
    LaunchProfile,
)
from services.retroarch.launcher import (
    RetroArchLauncher,
)


def test_launcher_builds_exact_core_rom_command():
    launcher = RetroArchLauncher()

    profile = LaunchProfile(
        game="Test Game",
        rom="/roms/Test Game.nes",
        core="/cores/fceumm_libretro.so",
    )

    with patch(
        "services.retroarch.launcher.subprocess.Popen"
    ) as popen:
        result = launcher.launch(
            profile
        )

    expected = [
        "retroarch",
        "-L",
        "/cores/fceumm_libretro.so",
        "/roms/Test Game.nes",
    ]

    popen.assert_called_once_with(
        expected
    )

    assert result == {
        "success": True,
        "command": expected,
    }


def test_launcher_appends_config_after_rom():
    launcher = RetroArchLauncher()

    profile = LaunchProfile(
        game="Configured Game",
        rom="/roms/game.sfc",
        core="/cores/snes9x_libretro.so",
        config="/configs/retrovault.cfg",
    )

    with patch(
        "services.retroarch.launcher.subprocess.Popen"
    ) as popen:
        result = launcher.launch(
            profile
        )

    expected = [
        "retroarch",
        "-L",
        "/cores/snes9x_libretro.so",
        "/roms/game.sfc",
        "--config",
        "/configs/retrovault.cfg",
    ]

    popen.assert_called_once_with(
        expected
    )

    assert result == {
        "success": True,
        "command": expected,
    }


def test_launcher_reports_process_spawn_failure():
    launcher = RetroArchLauncher()

    profile = LaunchProfile(
        game="Broken Game",
        rom="/roms/broken.nes",
        core="/cores/fceumm_libretro.so",
    )

    with patch(
        "services.retroarch.launcher.subprocess.Popen",
        side_effect=OSError(
            "process spawn failed"
        ),
    ) as popen:
        result = launcher.launch(
            profile
        )

    popen.assert_called_once_with(
        [
            "retroarch",
            "-L",
            "/cores/fceumm_libretro.so",
            "/roms/broken.nes",
        ]
    )

    assert result == {
        "success": False,
        "error": "process spawn failed",
    }


def test_launcher_appends_shader_after_rom():
    launcher = RetroArchLauncher()

    profile = LaunchProfile(
        game="Shader Game",
        rom="/roms/game.nes",
        core="/cores/fceumm_libretro.so",
        shader="/shaders/presets/console.slangp",
    )

    with patch(
        "services.retroarch.launcher.subprocess.Popen"
    ) as popen:
        result = launcher.launch(
            profile
        )

    expected = [
        "retroarch",
        "-L",
        "/cores/fceumm_libretro.so",
        "/roms/game.nes",
        "--set-shader",
        "/shaders/presets/console.slangp",
    ]

    popen.assert_called_once_with(
        expected
    )

    assert result == {
        "success": True,
        "command": expected,
    }


def test_launcher_composes_config_and_shader():
    launcher = RetroArchLauncher()

    profile = LaunchProfile(
        game="Presented Game",
        rom="/roms/game.sfc",
        core="/cores/snes9x_libretro.so",
        config="/configs/retrovault.cfg",
        shader="/shaders/presets/crt.slangp",
    )

    with patch(
        "services.retroarch.launcher.subprocess.Popen"
    ) as popen:
        result = launcher.launch(
            profile
        )

    expected = [
        "retroarch",
        "-L",
        "/cores/snes9x_libretro.so",
        "/roms/game.sfc",
        "--config",
        "/configs/retrovault.cfg",
        "--set-shader",
        "/shaders/presets/crt.slangp",
    ]

    popen.assert_called_once_with(
        expected
    )

    assert result == {
        "success": True,
        "command": expected,
    }
