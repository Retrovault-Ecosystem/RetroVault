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


class FakeOverlayRuntime:
    def __init__(
        self,
        runtime_file="/runtime/overlay.cfg",
    ):
        self.runtime_file = runtime_file
        self.calls = []

    def create(
        self,
        overlay,
    ):
        self.calls.append(
            overlay
        )

        return self.runtime_file


def test_launcher_appends_overlay_runtime_config():
    runtime = FakeOverlayRuntime()

    launcher = RetroArchLauncher(
        overlay_runtime=runtime
    )

    profile = LaunchProfile(
        game="Overlay Game",
        rom="/roms/game.nes",
        core="/cores/fceumm_libretro.so",
        overlay="/overlays/NES.cfg",
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
        "--appendconfig",
        "/runtime/overlay.cfg",
    ]

    assert runtime.calls == [
        "/overlays/NES.cfg"
    ]

    popen.assert_called_once_with(
        expected
    )

    assert result == {
        "success": True,
        "command": expected,
    }


def test_launcher_composes_config_overlay_and_shader():
    runtime = FakeOverlayRuntime(
        "/runtime/overlay.cfg"
    )

    launcher = RetroArchLauncher(
        overlay_runtime=runtime
    )

    profile = LaunchProfile(
        game="Presented Game",
        rom="/roms/game.sfc",
        core="/cores/snes9x_libretro.so",
        config="/configs/retrovault.cfg",
        overlay="/overlays/SNES.cfg",
        shader="/shaders/crt.slangp",
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
        "--appendconfig",
        "/runtime/overlay.cfg",
        "--set-shader",
        "/shaders/crt.slangp",
    ]

    popen.assert_called_once_with(
        expected
    )

    assert result == {
        "success": True,
        "command": expected,
    }


def test_launcher_reports_overlay_runtime_failure():
    class BrokenOverlayRuntime:
        def create(
            self,
            _overlay,
        ):
            raise ValueError(
                "broken overlay"
            )

    launcher = RetroArchLauncher(
        overlay_runtime=(
            BrokenOverlayRuntime()
        )
    )

    profile = LaunchProfile(
        game="Broken Overlay",
        rom="/roms/game.nes",
        core="/cores/fceumm_libretro.so",
        overlay="/overlays/broken.cfg",
    )

    with patch(
        "services.retroarch.launcher.subprocess.Popen"
    ) as popen:
        result = launcher.launch(
            profile
        )

    popen.assert_not_called()

    assert result == {
        "success": False,
        "error": "broken overlay",
    }


class FakeShaderRuntime:
    def __init__(
        self,
        parameters=None,
        runtime_shader="/runtime/shader.slangp",
    ):
        self.parameters = (
            {}
            if parameters is None
            else dict(parameters)
        )
        self.runtime_shader = runtime_shader
        self.parameter_calls = []
        self.resolve_calls = []

    def parameters_for_overlay(
        self,
        overlay,
    ):
        self.parameter_calls.append(
            overlay
        )

        return dict(
            self.parameters
        )

    def resolve(
        self,
        shader,
        parameters=None,
    ):
        self.resolve_calls.append(
            (
                shader,
                parameters,
            )
        )

        return self.runtime_shader


def test_launcher_shader_without_runtime_parameters_passes_through():
    shader_runtime = FakeShaderRuntime()

    launcher = RetroArchLauncher(
        shader_runtime=shader_runtime
    )

    profile = LaunchProfile(
        game="Shader Game",
        rom="/roms/game.nes",
        core="/cores/fceumm_libretro.so",
        shader="/shaders/base.slangp",
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
        "/shaders/base.slangp",
    ]

    assert shader_runtime.parameter_calls == [""]
    assert shader_runtime.resolve_calls == []

    popen.assert_called_once_with(
        expected
    )

    assert result == {
        "success": True,
        "command": expected,
    }


def test_launcher_wraps_selected_shader_when_overlay_has_parameters():
    overlay_runtime = FakeOverlayRuntime(
        "/runtime/overlay.cfg"
    )

    shader_runtime = FakeShaderRuntime(
        parameters={
            "PARAM": "1",
        },
        runtime_shader=(
            "/runtime/shader.slangp"
        ),
    )

    launcher = RetroArchLauncher(
        overlay_runtime=overlay_runtime,
        shader_runtime=shader_runtime,
    )

    profile = LaunchProfile(
        game="Presented Game",
        rom="/roms/game.nes",
        core="/cores/fceumm_libretro.so",
        overlay="/overlays/NES.cfg",
        shader="/shaders/base.slangp",
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
        "--appendconfig",
        "/runtime/overlay.cfg",
        "--set-shader",
        "/runtime/shader.slangp",
    ]

    assert shader_runtime.parameter_calls == [
        "/overlays/NES.cfg"
    ]

    assert shader_runtime.resolve_calls == [
        (
            "/shaders/base.slangp",
            {
                "PARAM": "1",
            },
        )
    ]

    popen.assert_called_once_with(
        expected
    )

    assert result == {
        "success": True,
        "command": expected,
    }


def test_launcher_does_not_synthesize_shader_for_overlay_only():
    shader_runtime = FakeShaderRuntime(
        parameters={
            "PARAM": "1",
        }
    )

    launcher = RetroArchLauncher(
        shader_runtime=shader_runtime
    )

    profile = LaunchProfile(
        game="Overlay Only",
        rom="/roms/game.nes",
        core="/cores/fceumm_libretro.so",
        overlay="",
        shader="",
    )

    with patch(
        "services.retroarch.launcher.subprocess.Popen"
    ) as popen:
        result = launcher.launch(
            profile
        )

    assert result["success"] is True

    assert shader_runtime.parameter_calls == []
    assert shader_runtime.resolve_calls == []

    popen.assert_called_once()


def test_launcher_reports_shader_runtime_failure():
    class BrokenShaderRuntime:
        def parameters_for_overlay(
            self,
            _overlay,
        ):
            raise ValueError(
                "broken shader runtime"
            )

        def resolve(
            self,
            shader,
            parameters=None,
        ):
            return shader

    launcher = RetroArchLauncher(
        shader_runtime=BrokenShaderRuntime()
    )

    profile = LaunchProfile(
        game="Broken Shader Runtime",
        rom="/roms/game.nes",
        core="/cores/fceumm_libretro.so",
        shader="/shaders/base.slangp",
    )

    with patch(
        "services.retroarch.launcher.subprocess.Popen"
    ) as popen:
        result = launcher.launch(
            profile
        )

    popen.assert_not_called()

    assert result == {
        "success": False,
        "error": "broken shader runtime",
    }
