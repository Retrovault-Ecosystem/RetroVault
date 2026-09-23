from unittest.mock import Mock, patch

from models.launch_profile import (
    LaunchProfile,
)
from services.retroarch.launcher import (
    RetroArchLauncher,
)


def test_launcher_builds_exact_core_rom_command():
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )

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
        expected,
        start_new_session=True,
    )

    assert result == {
        "success": True,
        "command": expected,
    }


def test_launcher_appends_config_after_rom():
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )

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
        expected,
        start_new_session=True,
    )

    assert result == {
        "success": True,
        "command": expected,
    }


def test_launcher_reports_process_spawn_failure():
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )

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
        ],
        start_new_session=True,
    )

    assert result == {
        "success": False,
        "error": "process spawn failed",
    }


def test_launcher_appends_shader_after_rom():
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )

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
        expected,
        start_new_session=True,
    )

    assert result == {
        "success": True,
        "command": expected,
    }


def test_launcher_composes_config_and_shader():
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )

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
        expected,
        start_new_session=True,
    )

    assert result == {
        "success": True,
        "command": expected,
    }


class FakeSessionConfig:
    """
    Preserve the pre-A.2 command expectations in tests that are not
    testing universal session isolation.

    Returning an empty path suppresses the session appendconfig for
    those focused unit tests. Dedicated A.2 tests below verify the
    production session contract explicitly.
    """

    def create(self, core_options_path=None):
        return ""


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
        session_config=FakeSessionConfig(),
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
        expected,
        start_new_session=True,
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
        session_config=FakeSessionConfig(),
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
        expected,
        start_new_session=True,
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
        session_config=FakeSessionConfig(),
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
        session_config=FakeSessionConfig(),
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
        expected,
        start_new_session=True,
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
        session_config=FakeSessionConfig(),
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
        expected,
        start_new_session=True,
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
        session_config=FakeSessionConfig(),
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
        session_config=FakeSessionConfig(),
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


def test_launcher_passes_explicit_archive_member_to_runtime():
    archive_runtime = Mock()

    archive_runtime.resolve.return_value = (
        "/tmp/runtime/Variant Game (J).nes"
    )

    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
        archive_runtime=archive_runtime,
    )

    profile = LaunchProfile(
        game="Variant Game",
        rom="/library/Variant Game.7z",
        core="/cores/fceumm_libretro.so",
        archive_member="Variant Game (J).nes",
    )

    with patch(
        "services.retroarch.launcher.subprocess.Popen"
    ) as popen:
        process = Mock()
        process.poll.return_value = None
        popen.return_value = process

        result = launcher.launch(profile)

    assert result["success"] is True

    archive_runtime.resolve.assert_called_once_with(
        "/library/Variant Game.7z",
        member="Variant Game (J).nes",
    )

    assert result["command"][:4] == [
        "retroarch",
        "-L",
        "/cores/fceumm_libretro.so",
        "/tmp/runtime/Variant Game (J).nes",
    ]


def test_launcher_preserves_automatic_archive_selection_by_default():
    archive_runtime = Mock()

    archive_runtime.resolve.return_value = (
        "/tmp/runtime/Variant Game (U) [!].nes"
    )

    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
        archive_runtime=archive_runtime,
    )

    profile = LaunchProfile(
        game="Variant Game",
        rom="/library/Variant Game.7z",
        core="/cores/fceumm_libretro.so",
    )

    with patch(
        "services.retroarch.launcher.subprocess.Popen"
    ) as popen:
        process = Mock()
        process.poll.return_value = None
        popen.return_value = process

        result = launcher.launch(profile)

    assert result["success"] is True

    archive_runtime.resolve.assert_called_once_with(
        "/library/Variant Game.7z",
        member=None,
    )


def test_launcher_appends_ephemeral_cheat_runtime(
    monkeypatch,
):
    class FakeArchiveRuntime:
        def resolve(
            self,
            rom,
            member=None,
        ):
            return rom

    class FakeCheatRuntime:
        def __init__(self):
            self.calls = []

        def create(
            self,
            cheat_file,
            core,
            runtime_rom,
        ):
            self.calls.append(
                (
                    cheat_file,
                    core,
                    runtime_rom,
                )
            )
            return "/runtime/cheats.cfg"

    cheat_runtime = FakeCheatRuntime()

    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
        archive_runtime=FakeArchiveRuntime(),
        cheat_runtime=cheat_runtime,
    )

    profile = LaunchProfile(
        game="Cheat Game",
        rom="/games/cheat-game.nes",
        core="/cores/nes.so",
        cheat_file="/tmp/cheat-game.cht",
    )

    process = Mock()
    process.poll.return_value = None

    popen = Mock(
        return_value=process
    )

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        popen,
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is True

    assert cheat_runtime.calls == [
        (
            "/tmp/cheat-game.cht",
            "/cores/nes.so",
            "/games/cheat-game.nes",
        )
    ]

    command = popen.call_args.args[0]

    assert "--appendconfig" in command

    index = command.index(
        "--appendconfig"
    )

    assert (
        command[index + 1]
        == "/runtime/cheats.cfg"
    )


def test_cheat_runtime_uses_game_specific_database_contract(
    tmp_path,
):
    from pathlib import Path

    from services.retroarch.cheat_runtime import (
        CheatRuntimeConfig,
    )

    info_root = tmp_path / "info"
    info_root.mkdir()

    (
        info_root
        / "snes9x_libretro.info"
    ).write_text(
        'corename = "Snes9x"\n',
        encoding="utf-8",
    )

    selected = tmp_path / "selected.cht"
    selected.write_text(
        (
            "cheats = 1\n"
            'cheat0_desc = "Test"\n'
            'cheat0_code = "AAAA-BBBB"\n'
            "cheat0_enable = true\n"
        ),
        encoding="utf-8",
    )

    runtime = CheatRuntimeConfig(
        runtime_root=(
            tmp_path
            / "runtime"
        ),
        info_roots=(
            info_root,
        ),
    )

    config = Path(
        runtime.create(
            selected,
            "/cores/snes9x_libretro.so",
            "/runtime/Super Mario World (USA).sfc",
        )
    )

    text = config.read_text(
        encoding="utf-8"
    )

    assert (
        "cheat_database_path"
        in text
    )
    assert (
        'apply_cheats_after_load = "true"'
        in text
    )
    assert "cheat_file =" not in text
    assert "cheat_apply_after_load" not in text

    database = (
        config.parent
        / "database"
        / "Snes9x"
        / "Super Mario World (USA).cht"
    )

    assert database.is_file()
    assert (
        database.read_text(
            encoding="utf-8"
        )
        == selected.read_text(
            encoding="utf-8"
        )
    )


def test_launcher_applies_clean_session_before_presentation(
    monkeypatch,
    tmp_path,
):
    """
    Every RetroVault-controlled launch receives the same clean
    presentation baseline before RetroVault overlay/shader state.

    This is content- and platform-independent.
    """
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import RetroArchLauncher

    calls = []

    class SessionConfig:
        def create(self, core_options_path=None):
            calls.append(
                "session"
            )
            return "/tmp/session.cfg"

    class OverlayRuntime:
        def create(
            self,
            overlay,
        ):
            calls.append(
                "overlay"
            )
            return "/tmp/overlay.cfg"

    class ShaderRuntime:
        @staticmethod
        def parameters_for_overlay(
            overlay,
        ):
            calls.append(
                "shader-parameters"
            )
            return {}

    class ArchiveRuntime:
        @staticmethod
        def resolve(
            rom,
            member=None,
        ):
            calls.append(
                "content"
            )
            return rom

    class Process:
        @staticmethod
        def poll():
            return None

    captured = {}

    def popen(command, **kwargs):
        assert kwargs == {
            "start_new_session": True,
        }
        captured["command"] = command
        return Process()

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        popen,
    )

    rom = tmp_path / "game.rom"
    rom.write_bytes(b"ROM")

    core = tmp_path / "core_libretro.so"
    core.write_bytes(b"CORE")

    overlay = tmp_path / "platform.cfg"
    overlay.write_text(
        "overlays = \"1\"\n",
        encoding="utf-8",
    )

    launcher = RetroArchLauncher(
        session_config=SessionConfig(),
        overlay_runtime=OverlayRuntime(),
        shader_runtime=ShaderRuntime(),
        archive_runtime=ArchiveRuntime(),
    )

    profile = LaunchProfile(
        game="Universal Test",
        rom=str(rom),
        core=str(core),
        overlay=str(overlay),
        shader="",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is True

    command = captured["command"]

    session_index = command.index(
        "/tmp/session.cfg"
    )

    overlay_index = command.index(
        "/tmp/overlay.cfg"
    )

    assert session_index < overlay_index

    assert calls[:3] == [
        "content",
        "session",
        "overlay",
    ]


def test_launcher_clean_session_is_game_name_independent(
    monkeypatch,
    tmp_path,
):
    """
    Different game identities must pass through the same universal
    RetroVault session-isolation boundary.
    """
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import RetroArchLauncher

    generated = []

    class SessionConfig:
        def create(self, core_options_path=None):
            generated.append(
                "session"
            )
            return "/tmp/session.cfg"

    class ArchiveRuntime:
        @staticmethod
        def resolve(
            rom,
            member=None,
        ):
            return rom

    class Process:
        @staticmethod
        def poll():
            return 0

    commands = []

    def popen(command, **kwargs):
        assert kwargs == {
            "start_new_session": True,
        }
        commands.append(
            command
        )
        return Process()

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        popen,
    )

    core = tmp_path / "core_libretro.so"
    core.write_bytes(b"CORE")

    launcher = RetroArchLauncher(
        session_config=SessionConfig(),
        archive_runtime=ArchiveRuntime(),
    )

    for name in (
        "Alpha Game",
        "Beta Game",
        "Completely Different Platform Game",
    ):
        rom = (
            tmp_path
            / f"{name}.rom"
        )

        rom.write_bytes(b"ROM")

        profile = LaunchProfile(
            game=name,
            rom=str(rom),
            core=str(core),
        )

        result = launcher.launch(
            profile
        )

        assert result["success"] is True

        launcher.clear_exited_process()

    assert generated == [
        "session",
        "session",
        "session",
    ]

    for command in commands:
        index = command.index(
            "--appendconfig"
        )

        assert command[
            index + 1
        ] == "/tmp/session.cfg"


def test_launch_injects_core_visible_area_policy_before_process(
    monkeypatch,
    tmp_path,
):
    from pathlib import Path
    from unittest.mock import Mock

    from services.retroarch.core_options_runtime import (
        CoreOptionsRuntimeConfig,
    )
    from services.retroarch.session_config import (
        RetroArchSessionConfig,
    )

    created = {}

    class Process:
        def poll(self):
            return None

    def fake_popen(command, **kwargs):
        assert kwargs == {
            "start_new_session": True,
        }
        created["command"] = command
        return Process()

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        fake_popen,
    )

    core_options = CoreOptionsRuntimeConfig(
        directory=(
            tmp_path
            / "core-options"
        )
    )

    sessions = RetroArchSessionConfig(
        directory=(
            tmp_path
            / "sessions"
        )
    )

    launcher = RetroArchLauncher(
        core_options_runtime=core_options,
        session_config=sessions,
    )

    profile = Mock()
    profile.core = "/cores/fceumm_libretro.so"
    profile.rom = "/games/example.nes"
    profile.source = ""
    profile.config = ""
    profile.overlay = ""
    profile.cheat_file = ""
    profile.shader = ""

    result = launcher.launch(
        profile
    )

    assert result["success"] is True

    command = created[
        "command"
    ]

    index = command.index(
        "--appendconfig"
    )

    session_path = Path(
        command[
            index + 1
        ]
    )

    payload = session_path.read_text(
        encoding="utf-8"
    )

    prefix = (
        'core_options_path = "'
    )

    option_line = next(
        line
        for line in payload.splitlines()
        if line.startswith(prefix)
    )

    options_path = Path(
        option_line[
            len(prefix):-1
        ]
    )

    assert options_path.is_file()

    assert options_path.read_text(
        encoding="utf-8"
    ) == (
        'fceumm_overscan_h_left = "0"\n'
        'fceumm_overscan_h_right = "0"\n'
        'fceumm_overscan_v_top = "0"\n'
        'fceumm_overscan_v_bottom = "0"\n'
    )

    assert (
        'global_core_options = "true"'
        in payload
    )

    core_options.cleanup()
    sessions.cleanup()


def test_launcher_forwards_platform_identity_to_core_options(
    monkeypatch,
):
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import RetroArchLauncher

    observed = {}

    class ArchiveRuntimeStub:
        def resolve(
            self,
            rom,
            member=None,
        ):
            return rom

    class CoreOptionsRuntimeStub:
        def create(
            self,
            core,
            platform_id=None,
        ):
            observed["core"] = core
            observed["platform_id"] = platform_id
            return None

    class SessionConfigStub:
        def create(
            self,
            core_options_path=None,
        ):
            return None

    class ProcessStub:
        pid = 43210

        def poll(self):
            return None

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        lambda *args, **kwargs: ProcessStub(),
    )

    launcher = RetroArchLauncher(
        archive_runtime=ArchiveRuntimeStub(),
        core_options_runtime=CoreOptionsRuntimeStub(),
        session_config=SessionConfigStub(),
    )

    profile = LaunchProfile(
        game="Platform Binding Test",
        rom="/roms/game.nes",
        core="/cores/fceumm_libretro.so",
        platform_id="platform.nintendo.nes",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is True

    assert observed == {
        "core": "/cores/fceumm_libretro.so",
        "platform_id": "platform.nintendo.nes",
    }


def test_launcher_maps_empty_platform_identity_to_legacy_none(
    monkeypatch,
):
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import RetroArchLauncher

    observed = {}

    class ArchiveRuntimeStub:
        def resolve(
            self,
            rom,
            member=None,
        ):
            return rom

    class CoreOptionsRuntimeStub:
        def create(
            self,
            core,
            platform_id=None,
        ):
            observed["platform_id"] = platform_id
            return None

    class SessionConfigStub:
        def create(
            self,
            core_options_path=None,
        ):
            return None

    class ProcessStub:
        pid = 43211

        def poll(self):
            return None

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        lambda *args, **kwargs: ProcessStub(),
    )

    launcher = RetroArchLauncher(
        archive_runtime=ArchiveRuntimeStub(),
        core_options_runtime=CoreOptionsRuntimeStub(),
        session_config=SessionConfigStub(),
    )

    profile = LaunchProfile(
        game="Legacy Binding Test",
        rom="/roms/game.nes",
        core="/cores/fceumm_libretro.so",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is True
    assert observed["platform_id"] is None
