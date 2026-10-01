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
        primary_config_runtime=FakePrimaryConfigRuntime(),
    )

    profile = LaunchProfile(
        game="Test Game",
        rom="/roms/Test Game.nes",
        core="/cores/fceumm_libretro.so",
    )

    with patch(
        "services.retroarch.launcher.subprocess.Popen"
    ) as popen:
        popen.return_value.poll.return_value = None
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


def test_launcher_isolates_explicit_primary_config():
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
        primary_config_runtime=FakePrimaryConfigRuntime(),
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
        popen.return_value.poll.return_value = None
        result = launcher.launch(
            profile
        )

    expected = [
        "retroarch", "--config", "/runtime/primary.cfg",
        "-L", "/cores/snes9x_libretro.so", "/roms/game.sfc",
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
        primary_config_runtime=FakePrimaryConfigRuntime(),
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
        popen.return_value.poll.return_value = None
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
        primary_config_runtime=FakePrimaryConfigRuntime(),
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
        popen.return_value.poll.return_value = None
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
        primary_config_runtime=FakePrimaryConfigRuntime(),
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
        popen.return_value.poll.return_value = None
        result = launcher.launch(
            profile
        )

    expected = [
        "retroarch",
        "--config",
        "/runtime/primary.cfg",
        "-L",
        "/cores/snes9x_libretro.so",
        "/roms/game.sfc",
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


class FakePrimaryConfigRuntime:
    """
    Preserve historical launcher command expectations in tests that are
    not specifically exercising early primary-config runtime authority.

    Dedicated tests inject their own PrimaryRuntime and verify the new
    production --config contract explicitly.
    """

    def create(self, *, source=None, overlay=None):
        return "/runtime/primary.cfg" if source else None


class FakeSessionConfig:
    """
    Preserve the pre-A.2 command expectations in tests that are not
    testing universal session isolation.

    Returning an empty path suppresses the session appendconfig for
    those focused unit tests. Dedicated A.2 tests below verify the
    production session contract explicitly.
    """

    def create(self, core_options_path=None, *, shader_enabled=False):
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
        primary_config_runtime=FakePrimaryConfigRuntime(),
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
        popen.return_value.poll.return_value = None
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
        primary_config_runtime=FakePrimaryConfigRuntime(),
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
        popen.return_value.poll.return_value = None
        result = launcher.launch(
            profile
        )

    expected = [
        "retroarch",
        "--config",
        "/runtime/primary.cfg",
        "-L",
        "/cores/snes9x_libretro.so",
        "/roms/game.sfc",
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
        primary_config_runtime=FakePrimaryConfigRuntime(),
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
        popen.return_value.poll.return_value = None
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
        primary_config_runtime=FakePrimaryConfigRuntime(),
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
        popen.return_value.poll.return_value = None
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
        primary_config_runtime=FakePrimaryConfigRuntime(),
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
        popen.return_value.poll.return_value = None
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
        primary_config_runtime=FakePrimaryConfigRuntime(),
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
        popen.return_value.poll.return_value = None
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
        primary_config_runtime=FakePrimaryConfigRuntime(),
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
        popen.return_value.poll.return_value = None
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
        primary_config_runtime=FakePrimaryConfigRuntime(),
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
        popen.return_value.poll.return_value = None
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
        primary_config_runtime=FakePrimaryConfigRuntime(),
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
        popen.return_value.poll.return_value = None
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
        primary_config_runtime=FakePrimaryConfigRuntime(),
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
        def create(self, core_options_path=None, *, shader_enabled=False):
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
        pid = 99999999
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

    assert command.count("--appendconfig") == 1
    assert command[command.index("--appendconfig") + 1].split("|") == [
        "/tmp/session.cfg",
        "/tmp/overlay.cfg",
    ]

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
        def create(self, core_options_path=None, *, shader_enabled=False):
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
        pid = 99999999
        returncode = None

        def poll(self):
            return self.returncode

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

        launcher.active_process.returncode = 0
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
        pid = 99999999
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
    profile.visual_tuning = ()

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
            shader_enabled=False,
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
        display_aspect_probe=A7StartupDisplayAspectProbe(),
        content_display_aspect_probe=A7ContentLoadedDisplayAspectProbe(),
        contain_runtime=A7StartupContainRuntime(),
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
            shader_enabled=False,
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


def test_a3n3b4_legacy_overlay_only_contract_is_unchanged(
    monkeypatch,
):
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    calls = []

    class OverlayRuntime:
        def create(
            self,
            overlay,
        ):
            calls.append(
                ("overlay", overlay)
            )
            return "/tmp/overlay-runtime.cfg"

    class SessionConfig:
        def create(
            self,
            core_options_path=None,
            shader_enabled=False,
        ):
            return None

    class Process:
        pid = 99999999
        def poll(self):
            return None

    popen_calls = []

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        lambda *args, **kwargs: (
            popen_calls.append(
                (args, kwargs)
            )
            or Process()
        ),
    )

    launcher = RetroArchLauncher(
        session_config=SessionConfig(),
        overlay_runtime=OverlayRuntime(),
    )

    profile = LaunchProfile(
        game="Legacy Overlay",
        rom="/roms/game.nes",
        core="/cores/fceumm_libretro.so",
        overlay="/legacy/NES.cfg",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is True
    assert calls == [
        (
            "overlay",
            "/legacy/NES.cfg",
        )
    ]
    assert len(popen_calls) == 1


def test_a3n3b4_legacy_shader_only_contract_is_unchanged(
    monkeypatch,
):
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    class SessionConfig:
        def create(
            self,
            core_options_path=None,
            shader_enabled=False,
        ):
            return None

    class Process:
        pid = 99999999
        def poll(self):
            return None

    popen_calls = []

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        lambda *args, **kwargs: (
            popen_calls.append(
                (args, kwargs)
            )
            or Process()
        ),
    )

    launcher = RetroArchLauncher(
        session_config=SessionConfig(),
    )

    profile = LaunchProfile(
        game="Legacy Shader",
        rom="/roms/game.nes",
        core="/cores/fceumm_libretro.so",
        shader="/legacy/base.slangp",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is True
    assert len(popen_calls) == 1


def test_a3n3b4_non_string_platform_keeps_legacy_contract(
    monkeypatch,
):
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    class SessionConfig:
        def create(
            self,
            core_options_path=None,
            shader_enabled=False,
        ):
            return None

    class Process:
        pid = 99999999
        def poll(self):
            return None

    popen_calls = []

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        lambda *args, **kwargs: (
            popen_calls.append(
                (args, kwargs)
            )
            or Process()
        ),
    )

    launcher = RetroArchLauncher(
        session_config=SessionConfig(),
    )

    profile = LaunchProfile(
        game="Legacy Non-string",
        rom="/roms/game.nes",
        core="/cores/fceumm_libretro.so",
        shader="/legacy/base.slangp",
    )

    profile.platform_id = object()

    result = launcher.launch(
        profile
    )

    assert result["success"] is True
    assert len(popen_calls) == 1


def test_a3n3b4_unknown_string_platform_keeps_legacy_contract(
    monkeypatch,
):
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    class SessionConfig:
        def create(
            self,
            core_options_path=None,
            shader_enabled=False,
        ):
            return None

    class Process:
        pid = 99999999
        def poll(self):
            return None

    popen_calls = []

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        lambda *args, **kwargs: (
            popen_calls.append(
                (args, kwargs)
            )
            or Process()
        ),
    )

    launcher = RetroArchLauncher(
        session_config=SessionConfig(),
    )

    profile = LaunchProfile(
        game="Unknown Platform",
        rom="/roms/game.nes",
        core="/cores/unknown_libretro.so",
        shader="/legacy/base.slangp",
        platform_id="platform.unknown.test",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is True
    assert len(popen_calls) == 1


def test_a3n3b4_canonical_identity_without_assets_preserves_core_policy_path(
    monkeypatch,
):
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    observed = {}

    class CoreOptions:
        def create(
            self,
            core,
            platform_id=None,
        ):
            observed["core"] = core
            observed["platform_id"] = platform_id
            return None

    class SessionConfig:
        def create(
            self,
            core_options_path=None,
            shader_enabled=False,
        ):
            return None

    class Process:
        pid = 99999999
        def poll(self):
            return None

    popen_calls = []

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        lambda *args, **kwargs: (
            popen_calls.append(
                (args, kwargs)
            )
            or Process()
        ),
    )

    launcher = RetroArchLauncher(
        display_aspect_probe=A7StartupDisplayAspectProbe(),
        content_display_aspect_probe=A7ContentLoadedDisplayAspectProbe(),
        contain_runtime=A7StartupContainRuntime(),
        core_options_runtime=CoreOptions(),
        session_config=SessionConfig(),
    )

    profile = LaunchProfile(
        game="Canonical Policy Only",
        rom="/roms/game.nes",
        core="/cores/fceumm_libretro.so",
        platform_id="platform.nintendo.nes",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is True
    assert (
        observed["platform_id"]
        == "platform.nintendo.nes"
    )
    assert len(popen_calls) == 1


def test_a3n3b4_ready_partial_launchprofile_package_does_not_override_canonical_ready_authority(
    monkeypatch,
):
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import RetroArchLauncher

    observed = {}

    class CanonicalPackage:
        overlay = "/canonical/nes/RetroVault_NES_Classic.cfg"
        shader = "/canonical/nes/RetroVault_NES_Classic_CRT.slangp"

    def resolve(**kwargs):
        observed.update(kwargs)
        return CanonicalPackage()

    monkeypatch.setattr(
        "services.retroarch.launcher."
        "CanonicalProductionPackageResolver.resolve",
        resolve,
    )

    archive_calls = []

    class ArchiveRuntime:
        def resolve(self, rom, *, member=None):
            archive_calls.append((rom, member))
            return rom

    class StopBeforeRuntime:
        def create(self, *args, **kwargs):
            raise ValueError("test stop after canonical authority")

        def cleanup(self, *args, **kwargs):
            return None

    launcher = RetroArchLauncher(
        archive_runtime=ArchiveRuntime(),
        primary_config_runtime=StopBeforeRuntime(),
    )

    profile = LaunchProfile(
        game="Canonical Partial",
        rom="/roms/game.nes",
        core="fceumm",
        overlay="/legacy/content-specific.cfg",
        shader="",
        platform_id="platform.nintendo.nes",
    )

    result = launcher.launch(profile)

    assert isinstance(observed.pop("config"), dict)
    assert observed == {
        "platform_id": "platform.nintendo.nes",
        "core_identity": "fceumm",
    }
    assert archive_calls == [
        ("/roms/game.nes", None),
    ]
    assert result == {
        "success": False,
        "error": "test stop after canonical authority",
    }


def test_ready_platform_rejects_foreign_core_package_before_archive(
    monkeypatch,
):
    from pathlib import Path

    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    root = Path(__file__).resolve().parents[1]

    overlay = (
        root
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic.cfg"
    )

    shader = (
        root
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic_CRT.slangp"
    )

    calls = []

    class ArchiveRuntime:
        def resolve(
            self,
            *args,
            **kwargs,
        ):
            calls.append("archive")
            raise AssertionError(
                "archive resolution must not occur"
            )

    launcher = RetroArchLauncher(
        archive_runtime=ArchiveRuntime(),
    )

    profile = LaunchProfile(
        game="Genesis Foreign Package",
        rom="/roms/game.bin",
        core="fceumm",
        overlay=str(overlay),
        shader=str(shader),
        platform_id="platform.sega.genesis",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is False
    assert result["error"] == "Core fceumm is not eligible for platform.sega.genesis."
    assert calls == []


def test_a3n3b4_ready_platform_ignores_foreign_launchprofile_package_metadata(
    monkeypatch,
):
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import RetroArchLauncher

    observed = {}

    class CanonicalPackage:
        overlay = "/canonical/nes/RetroVault_NES_Classic.cfg"
        shader = "/canonical/nes/RetroVault_NES_Classic_CRT.slangp"

    def resolve(**kwargs):
        observed.update(kwargs)
        return CanonicalPackage()

    monkeypatch.setattr(
        "services.retroarch.launcher."
        "CanonicalProductionPackageResolver.resolve",
        resolve,
    )

    archive_calls = []

    class ArchiveRuntime:
        def resolve(self, rom, *, member=None):
            archive_calls.append((rom, member))
            return rom

    class StopBeforeRuntime:
        def create(self, *args, **kwargs):
            raise ValueError("test stop after canonical authority")

        def cleanup(self, *args, **kwargs):
            return None

    launcher = RetroArchLauncher(
        archive_runtime=ArchiveRuntime(),
        primary_config_runtime=StopBeforeRuntime(),
    )

    profile = LaunchProfile(
        game="NES Foreign Legacy Metadata",
        rom="/roms/game.nes",
        core="fceumm",
        overlay="/legacy/snes/RetroVault_SNES_Classic.cfg",
        shader="/legacy/snes/RetroVault_SNES_Classic_CRT.slangp",
        platform_id="platform.nintendo.nes",
    )

    result = launcher.launch(profile)

    assert isinstance(observed.pop("config"), dict)
    assert observed == {
        "platform_id": "platform.nintendo.nes",
        "core_identity": "fceumm",
    }
    assert archive_calls == [
        ("/roms/game.nes", None),
    ]
    assert result == {
        "success": False,
        "error": "test stop after canonical authority",
    }


def test_a3n3b4_ready_platform_foreign_core_fails_before_archive(
    monkeypatch,
):
    from pathlib import Path

    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    root = Path(__file__).resolve().parents[1]

    overlay = (
        root
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic.cfg"
    )

    shader = (
        root
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic_CRT.slangp"
    )

    calls = []

    class ArchiveRuntime:
        def resolve(
            self,
            *args,
            **kwargs,
        ):
            calls.append("archive")
            raise AssertionError(
                "archive resolution must not occur"
            )

    launcher = RetroArchLauncher(
        archive_runtime=ArchiveRuntime(),
    )

    profile = LaunchProfile(
        game="NES Foreign Core",
        rom="/roms/game.nes",
        core="snes9x",
        overlay=str(overlay),
        shader=str(shader),
        platform_id="platform.nintendo.nes",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is False
    assert calls == []


def test_a3n3b4_valid_nes_package_passes_gate_before_archive(
    monkeypatch,
):
    from pathlib import Path

    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    root = Path(__file__).resolve().parents[1]

    overlay = (
        root
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic.cfg"
    )

    shader = (
        root
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic_CRT.slangp"
    )

    calls = []

    class ArchiveRuntime:
        def resolve(
            self,
            rom,
            member=None,
        ):
            calls.append("archive")
            return rom

    class CoreOptions:
        def create(
            self,
            core,
            platform_id=None,
        ):
            calls.append(
                (
                    "core_options",
                    platform_id,
                )
            )
            return None

    class SessionConfig:
        def create(
            self,
            core_options_path=None,
            shader_enabled=False,
        ):
            calls.append("session")
            return None

    class OverlayRuntime:
        def create(
            self,
            value,
        ):
            calls.append("overlay")
            return "/tmp/overlay-runtime.cfg"

    class ShaderRuntime:
        def parameters_for_overlay(
            self,
            value,
        ):
            calls.append("shader_parameters")
            return {}

        def resolve(
            self,
            shader,
            parameters,
        ):
            raise AssertionError(
                "resolve should not be required"
            )

    class Process:
        pid = 99999999
        def poll(self):
            return None

    popen_calls = []

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        lambda *args, **kwargs: (
            popen_calls.append(
                (args, kwargs)
            )
            or Process()
        ),
    )

    launcher = RetroArchLauncher(
        display_aspect_probe=A7StartupDisplayAspectProbe(),
        content_display_aspect_probe=A7ContentLoadedDisplayAspectProbe(),
        contain_runtime=A7StartupContainRuntime(),
        archive_runtime=ArchiveRuntime(),
        core_options_runtime=CoreOptions(),
        session_config=SessionConfig(),
        overlay_runtime=OverlayRuntime(),
        shader_runtime=ShaderRuntime(),
    )

    profile = LaunchProfile(
        game="Valid NES Package",
        rom="/roms/game.nes",
        core="fceumm",
        overlay=str(overlay),
        shader=str(shader),
        platform_id="platform.nintendo.nes",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is True
    assert calls[0] == "archive"
    assert (
        "core_options",
        "platform.nintendo.nes",
    ) in calls
    assert len(popen_calls) == 1


def test_a3n3b4_valid_snes_package_passes_gate_before_archive(
    monkeypatch,
):
    from pathlib import Path

    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    root = Path(__file__).resolve().parents[1]

    overlay = (
        root
        / "retrovault"
        / "snes"
        / "classic"
        / "RetroVault_SNES_Classic.cfg"
    )

    shader = (
        root
        / "retrovault"
        / "snes"
        / "classic"
        / "RetroVault_SNES_Classic_CRT.slangp"
    )

    class ArchiveRuntime:
        def resolve(
            self,
            rom,
            member=None,
        ):
            return rom

    class CoreOptions:
        def create(
            self,
            core,
            platform_id=None,
        ):
            return None

    class SessionConfig:
        def create(
            self,
            core_options_path=None,
            shader_enabled=False,
        ):
            return None

    class OverlayRuntime:
        def create(
            self,
            value,
        ):
            return "/tmp/overlay-runtime.cfg"

    class ShaderRuntime:
        def parameters_for_overlay(
            self,
            value,
        ):
            return {}

        def resolve(
            self,
            shader,
            parameters,
        ):
            raise AssertionError(
                "resolve should not be required"
            )

    class Process:
        pid = 99999999
        def poll(self):
            return None

    popen_calls = []

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        lambda *args, **kwargs: (
            popen_calls.append(
                (args, kwargs)
            )
            or Process()
        ),
    )

    launcher = RetroArchLauncher(
        display_aspect_probe=A7StartupDisplayAspectProbe(),
        content_display_aspect_probe=A7ContentLoadedDisplayAspectProbe(),
        contain_runtime=A7StartupContainRuntime(),
        archive_runtime=ArchiveRuntime(),
        core_options_runtime=CoreOptions(),
        session_config=SessionConfig(),
        overlay_runtime=OverlayRuntime(),
        shader_runtime=ShaderRuntime(),
    )

    profile = LaunchProfile(
        game="Valid SNES Package",
        rom="/roms/game.sfc",
        core="snes9x",
        overlay=str(overlay),
        shader=str(shader),
        platform_id="platform.nintendo.snes",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is True
    assert len(popen_calls) == 1


def test_ready_nes_production_package_accepts_absolute_core_path(
    monkeypatch,
):
    from pathlib import Path

    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    root = Path(__file__).resolve().parents[1]

    overlay = (
        root
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic.cfg"
    )

    shader = (
        root
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic_CRT.slangp"
    )

    executable_core = (
        "/opt/retropie/libretrocores/lr-fceumm/"
        "fceumm_libretro.so"
    )

    class ArchiveRuntime:
        def resolve(
            self,
            rom,
            member=None,
        ):
            return rom

    class CoreOptions:
        def create(
            self,
            core,
            platform_id=None,
        ):
            assert core == executable_core
            assert (
                platform_id
                == "platform.nintendo.nes"
            )
            return None

    class SessionConfig:
        def create(
            self,
            core_options_path=None,
            shader_enabled=False,
        ):
            return None

    class OverlayRuntime:
        def create(
            self,
            value,
        ):
            return "/tmp/overlay-runtime.cfg"

    class ShaderRuntime:
        def parameters_for_overlay(
            self,
            value,
        ):
            return {}

        def resolve(
            self,
            shader,
            parameters,
        ):
            raise AssertionError(
                "Shader resolution should not be required."
            )

    class Process:
        pid = 99999999
        def poll(self):
            return None

    popen_calls = []

    def fake_popen(
        command,
        **kwargs,
    ):
        popen_calls.append(
            (
                command,
                kwargs,
            )
        )
        return Process()

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        fake_popen,
    )

    launcher = RetroArchLauncher(
        display_aspect_probe=A7StartupDisplayAspectProbe(),
        content_display_aspect_probe=A7ContentLoadedDisplayAspectProbe(),
        contain_runtime=A7StartupContainRuntime(),
        archive_runtime=ArchiveRuntime(),
        core_options_runtime=CoreOptions(),
        session_config=SessionConfig(),
        primary_config_runtime=FakePrimaryConfigRuntime(),
        overlay_runtime=OverlayRuntime(),
        shader_runtime=ShaderRuntime(),
    )

    profile = LaunchProfile(
        game="NES Absolute Core",
        rom="/roms/game.nes",
        core=executable_core,
        overlay=str(overlay),
        shader=str(shader),
        platform_id="platform.nintendo.nes",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is True
    assert len(popen_calls) == 1

    command = popen_calls[0][0]

    assert command[:4] == [
        "retroarch",
        "-L",
        executable_core,
        "/roms/game.nes",
    ]


def test_ready_snes_production_package_accepts_absolute_core_path(
    monkeypatch,
):
    from pathlib import Path

    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    root = Path(__file__).resolve().parents[1]

    overlay = (
        root
        / "retrovault"
        / "snes"
        / "classic"
        / "RetroVault_SNES_Classic.cfg"
    )

    shader = (
        root
        / "retrovault"
        / "snes"
        / "classic"
        / "RetroVault_SNES_Classic_CRT.slangp"
    )

    executable_core = (
        "/opt/retropie/libretrocores/lr-snes9x/"
        "snes9x_libretro.so"
    )

    class ArchiveRuntime:
        def resolve(
            self,
            rom,
            member=None,
        ):
            return rom

    class CoreOptions:
        def create(
            self,
            core,
            platform_id=None,
        ):
            assert core == executable_core
            assert (
                platform_id
                == "platform.nintendo.snes"
            )
            return None

    class SessionConfig:
        def create(
            self,
            core_options_path=None,
            shader_enabled=False,
        ):
            return None

    class OverlayRuntime:
        def create(
            self,
            value,
        ):
            return "/tmp/overlay-runtime.cfg"

    class ShaderRuntime:
        def parameters_for_overlay(
            self,
            value,
        ):
            return {}

        def resolve(
            self,
            shader,
            parameters,
        ):
            raise AssertionError(
                "Shader resolution should not be required."
            )

    class Process:
        pid = 99999999
        def poll(self):
            return None

    popen_calls = []

    def fake_popen(
        command,
        **kwargs,
    ):
        popen_calls.append(
            (
                command,
                kwargs,
            )
        )
        return Process()

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        fake_popen,
    )

    launcher = RetroArchLauncher(
        display_aspect_probe=A7StartupDisplayAspectProbe(),
        content_display_aspect_probe=A7ContentLoadedDisplayAspectProbe(),
        contain_runtime=A7StartupContainRuntime(),
        archive_runtime=ArchiveRuntime(),
        core_options_runtime=CoreOptions(),
        session_config=SessionConfig(),
        primary_config_runtime=FakePrimaryConfigRuntime(),
        overlay_runtime=OverlayRuntime(),
        shader_runtime=ShaderRuntime(),
    )

    profile = LaunchProfile(
        game="SNES Absolute Core",
        rom="/roms/game.sfc",
        core=executable_core,
        overlay=str(overlay),
        shader=str(shader),
        platform_id="platform.nintendo.snes",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is True
    assert len(popen_calls) == 1

    command = popen_calls[0][0]

    assert command[:4] == [
        "retroarch",
        "-L",
        executable_core,
        "/roms/game.sfc",
    ]


def test_wayland_primary_runtime_precedes_core_and_append_configs(
    monkeypatch,
):
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    class PrimaryRuntime:
        def create(self, *, overlay=None):
            return "/runtime/primary.cfg"

    class SessionConfig:
        def create(
            self,
            core_options_path=None,
            shader_enabled=False,
        ):
            return "/runtime/session.cfg"

    class Process:
        pid = 99999999
        def poll(self):
            return None

    popen_calls = []

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        lambda command, **kwargs: (
            popen_calls.append(
                (
                    command,
                    kwargs,
                )
            )
            or Process()
        ),
    )

    launcher = RetroArchLauncher(
        primary_config_runtime=PrimaryRuntime(),
        session_config=SessionConfig(),
    )

    profile = LaunchProfile(
        game="Primary Runtime",
        rom="/roms/game.bin",
        core="/cores/example_libretro.so",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is True
    assert len(popen_calls) == 1

    command = popen_calls[0][0]

    assert command[:7] == [
        "retroarch",
        "--config",
        "/runtime/primary.cfg",
        "-L",
        "/cores/example_libretro.so",
        "/roms/game.bin",
        "--appendconfig",
    ]

    assert (
        command[7]
        == "/runtime/session.cfg"
    )


def test_launchprofile_config_is_source_for_one_isolated_primary(
    monkeypatch,
):
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    class PrimaryRuntime:
        def create(self, *, source=None, overlay=None):
            assert source == "/user/extra.cfg"
            return "/runtime/primary.cfg"

    class SessionConfig:
        def create(
            self,
            core_options_path=None,
            shader_enabled=False,
        ):
            return "/runtime/session.cfg"

    class Process:
        pid = 99999999
        def poll(self):
            return None

    popen_calls = []

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        lambda command, **kwargs: (
            popen_calls.append(
                (
                    command,
                    kwargs,
                )
            )
            or Process()
        ),
    )

    launcher = RetroArchLauncher(
        primary_config_runtime=PrimaryRuntime(),
        session_config=SessionConfig(),
    )

    profile = LaunchProfile(
        game="Explicit Config",
        rom="/roms/game.bin",
        core="/cores/example_libretro.so",
        config="/user/extra.cfg",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is True

    command = popen_calls[0][0]

    # The transient primary configuration must be selected first so
    # early video initialization sees GLCore.
    assert command[:6] == [
        "retroarch",
        "--config",
        "/runtime/primary.cfg",
        "-L",
        "/cores/example_libretro.so",
        "/roms/game.bin",
    ]

    assert command.count("--config") == 1
    assert "/user/extra.cfg" not in command

    assert [
        "--appendconfig",
        "/runtime/session.cfg",
    ] == command[
        command.index(
            "/runtime/session.cfg"
        ) - 1:
        command.index(
            "/runtime/session.cfg"
        ) + 1
    ]


def test_primary_runtime_failure_is_fail_closed_before_popen(
    monkeypatch,
):
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    class PrimaryRuntime:
        def create(self, *, overlay=None):
            raise ValueError(
                "primary runtime unavailable"
            )

    popen_calls = []

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        lambda *args, **kwargs: (
            popen_calls.append(
                (
                    args,
                    kwargs,
                )
            )
        ),
    )

    launcher = RetroArchLauncher(
        primary_config_runtime=PrimaryRuntime(),
    )

    profile = LaunchProfile(
        game="Primary Failure",
        rom="/roms/game.bin",
        core="/cores/example_libretro.so",
    )

    result = launcher.launch(
        profile
    )

    assert result["success"] is False
    assert (
        result["error"]
        == "primary runtime unavailable"
    )
    assert popen_calls == []


class A7StartupDisplayAspect:
    width = 1.306
    height = 1.0

    @property
    def ratio(self):
        return self.width / self.height


class A7StartupDisplayAspectProbe:
    def __init__(self):
        self.cores = []

    def acquire(self, core):
        self.cores.append(core)
        return A7StartupDisplayAspect()


class A7ContentLoadedDisplayAspectProbe:
    def __init__(self, ratio=4 / 3):
        self.ratio = ratio
        self.calls = []

    def acquire(
        self,
        *,
        command,
        core,
        content,
        prefix_args=(),
        append_configs=(),
        shader=None,
    ):
        from services.retroarch.display_aspect import (
            CoreDisplayAspect,
        )

        self.calls.append(
            {
                "command": command,
                "core": core,
                "content": content,
                "prefix_args": tuple(prefix_args),
                "append_configs": tuple(append_configs),
                "shader": shader,
            }
        )

        return CoreDisplayAspect(
            width=self.ratio,
            height=1.0,
        )


class A7StartupContainRuntime:
    def __init__(self):
        self.calls = []

    def create_for_aspect(
        self,
        *,
        profile,
        display_aspect,
    ):
        self.calls.append(
            {
                "profile": profile,
                "display_aspect": display_aspect,
            }
        )

        return "/tmp/retrovault-a7-startup-contain.cfg"

    def cleanup(self, path=None):
        return None


def test_a7_startup_dependencies_are_injectable():
    from services.retroarch.launcher import RetroArchLauncher

    probe = A7StartupDisplayAspectProbe()
    contain = A7StartupContainRuntime()

    launcher = RetroArchLauncher(
        display_aspect_probe=probe,
        contain_runtime=contain,
    )

    assert launcher.display_aspect_probe is probe
    assert launcher.contain_runtime is contain


def test_a7_startup_contain_is_created_before_process_start():
    import inspect

    from services.retroarch.launcher import RetroArchLauncher

    source = inspect.getsource(
        RetroArchLauncher.launch
    )

    assert (
        source.index("create_for_aspect")
        < source.index("subprocess.Popen")
    )


def test_a7_startup_contain_is_final_geometry_append():
    import inspect

    from services.retroarch.launcher import RetroArchLauncher

    source = inspect.getsource(
        RetroArchLauncher.launch
    )

    assert (
        source.index("self.overlay_runtime.create")
        < source.index("create_for_aspect")
    )


def test_a7_launcher_has_no_content_specific_geometry():
    from pathlib import Path

    source = Path(
        "services/retroarch/launcher.py"
    ).read_text(
        encoding="utf-8"
    ).casefold()

    for forbidden in (
        "duck tales",
        "ducktales",
        "street fighter",
        "super mario",
        "sonic the hedgehog",
    ):
        assert forbidden not in source


def test_ready_platform_launch_does_not_require_content_named_runtime_descriptor():
    """
    READY production presentation is platform-authoritative.

    A historical content-specific overlay path must not become the package
    identity used by production-package validation.  The launcher must
    resolve the canonical platform production package instead of deriving
    a sibling runtime descriptor from per-content artwork metadata.
    """
    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
    )

    ready = set(
        PlatformPresentationPolicyRegistry.ready_platform_ids()
    )

    assert "platform.nintendo.nes" in ready
    assert "platform.nintendo.snes" in ready


def test_process_group_exists_reports_live_and_missing_groups(
    monkeypatch,
):
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    calls = []

    def fake_killpg(process_group, signal_number):
        calls.append(
            (
                process_group,
                signal_number,
            )
        )

        if process_group == 222:
            raise ProcessLookupError

    monkeypatch.setattr(
        "services.retroarch.launcher.os.killpg",
        fake_killpg,
    )

    assert (
        RetroArchLauncher._process_group_exists(
            111
        )
        is True
    )

    assert (
        RetroArchLauncher._process_group_exists(
            222
        )
        is False
    )

    assert calls == [
        (111, 0),
        (222, 0),
    ]


def test_stop_escalates_when_wrapper_exits_before_process_group(
    monkeypatch,
):
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    class Process:
        pid = 99999999
        pid = 12345

        def __init__(self):
            self.returncode = None
            self.wait_calls = []

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            self.wait_calls.append(
                timeout
            )

            self.returncode = -15

            return self.returncode

    process = Process()

    launcher = object.__new__(
        RetroArchLauncher
    )

    launcher._active_process = process
    launcher._active_primary_config = None
    launcher._active_contain_config = None

    cleanup_calls = []

    launcher._cleanup_active_transients = (
        lambda: cleanup_calls.append(
            True
        )
    )

    signals = []

    monkeypatch.setattr(
        "services.retroarch.launcher.os.getpgid",
        lambda pid: 54321,
    )

    monkeypatch.setattr(
        "services.retroarch.launcher.os.killpg",
        lambda pgid, sig: signals.append(
            (
                pgid,
                sig,
            )
        ),
    )

    group_waits = iter(
        [
            False,
            True,
        ]
    )

    monkeypatch.setattr(
        launcher,
        "_wait_for_process_group_exit",
        lambda process_group, **kwargs: next(
            group_waits
        ),
    )

    assert launcher.stop() is True

    import signal

    assert signals == [
        (
            54321,
            signal.SIGTERM,
        ),
        (
            54321,
            signal.SIGKILL,
        ),
    ]

    assert process.wait_calls == [
        5.0,
    ]

    assert cleanup_calls == [
        True,
    ]

    assert (
        launcher._active_process
        is None
    )


def test_stop_does_not_escalate_when_complete_group_exits(
    monkeypatch,
):
    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    class Process:
        pid = 99999999
        pid = 12345

        def __init__(self):
            self.returncode = None

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            self.returncode = -15
            return self.returncode

    process = Process()

    launcher = object.__new__(
        RetroArchLauncher
    )

    launcher._active_process = process
    launcher._active_primary_config = None
    launcher._active_contain_config = None

    launcher._cleanup_active_transients = (
        lambda: None
    )

    signals = []

    monkeypatch.setattr(
        "services.retroarch.launcher.os.getpgid",
        lambda pid: 54321,
    )

    monkeypatch.setattr(
        "services.retroarch.launcher.os.killpg",
        lambda pgid, sig: signals.append(
            (
                pgid,
                sig,
            )
        ),
    )

    monkeypatch.setattr(
        launcher,
        "_wait_for_process_group_exit",
        lambda process_group, **kwargs: True,
    )

    assert launcher.stop() is True

    import signal

    assert signals == [
        (
            54321,
            signal.SIGTERM,
        ),
    ]


def test_stop_refuses_to_cleanup_if_process_group_survives_sigkill(
    monkeypatch,
):
    import pytest

    from services.retroarch.launcher import (
        RetroArchLauncher,
    )

    class Process:
        pid = 99999999
        pid = 12345

        def __init__(self):
            self.returncode = None

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            self.returncode = -15
            return self.returncode

    process = Process()

    launcher = object.__new__(
        RetroArchLauncher
    )

    launcher._active_process = process
    launcher._active_primary_config = None
    launcher._active_contain_config = None

    cleanup_calls = []

    launcher._cleanup_active_transients = (
        lambda: cleanup_calls.append(
            True
        )
    )

    monkeypatch.setattr(
        "services.retroarch.launcher.os.getpgid",
        lambda pid: 54321,
    )

    monkeypatch.setattr(
        "services.retroarch.launcher.os.killpg",
        lambda pgid, sig: None,
    )

    monkeypatch.setattr(
        launcher,
        "_wait_for_process_group_exit",
        lambda process_group, **kwargs: False,
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "RetroArch process group did not "
            "terminate completely"
        ),
    ):
        launcher.stop()

    assert cleanup_calls == []


def test_a3n5e_cleanup_owns_all_one_launch_runtime_services(
    tmp_path,
):
    from services.retroarch.launcher import RetroArchLauncher

    class PrimaryRuntime:
        def __init__(self):
            self.cleaned = []

        def cleanup(self, path):
            self.cleaned.append(path)

    class ServiceRuntime:
        def __init__(self):
            self.cleanup_calls = 0

        def cleanup(self):
            self.cleanup_calls += 1

    launcher = object.__new__(
        RetroArchLauncher
    )

    launcher.primary_config_runtime = PrimaryRuntime()
    launcher.core_options_runtime = ServiceRuntime()
    launcher.session_config = ServiceRuntime()
    launcher.overlay_runtime = ServiceRuntime()
    launcher.adaptive_bezel_runtime = ServiceRuntime()
    launcher.contain_runtime = ServiceRuntime()
    launcher.shader_runtime = ServiceRuntime()

    launcher._active_primary_config = (
        "/tmp/retrovault-primary.cfg"
    )
    launcher._active_contain_config = (
        "/tmp/retrovault-contain.cfg"
    )

    cheat_root = (
        tmp_path
        / "retrovault-cheats-a3n5e"
    )

    cheat_root.mkdir()

    cheat_config = (
        cheat_root
        / "retroarch-cheats.cfg"
    )

    cheat_config.write_text(
        'apply_cheats_after_load = "true"\n',
        encoding="utf-8",
    )

    from services.retroarch.cheat_runtime import CheatRuntimeConfig
    launcher.cheat_runtime = CheatRuntimeConfig(runtime_root=tmp_path)
    launcher.cheat_runtime._created.append(cheat_root)
    launcher._active_cheat_config = str(cheat_config)

    launcher._cleanup_active_transients()

    assert (
        launcher.primary_config_runtime.cleaned
        == ["/tmp/retrovault-primary.cfg"]
    )

    for runtime in (
        launcher.core_options_runtime,
        launcher.session_config,
        launcher.overlay_runtime,
        launcher.adaptive_bezel_runtime,
        launcher.contain_runtime,
        launcher.shader_runtime,
    ):
        assert runtime.cleanup_calls == 1

    assert not cheat_root.exists()

    assert launcher._active_primary_config is None
    assert launcher._active_contain_config is None
    assert launcher._active_cheat_config is None


def test_a3n5e_cleanup_preserves_archive_cache(
    tmp_path,
):
    from services.retroarch.launcher import RetroArchLauncher

    class PrimaryRuntime:
        def cleanup(self, _path):
            pass

    class ServiceRuntime:
        def cleanup(self):
            pass

    launcher = object.__new__(
        RetroArchLauncher
    )

    launcher.primary_config_runtime = PrimaryRuntime()
    launcher.core_options_runtime = ServiceRuntime()
    launcher.session_config = ServiceRuntime()
    launcher.overlay_runtime = ServiceRuntime()
    launcher.adaptive_bezel_runtime = ServiceRuntime()
    launcher.contain_runtime = ServiceRuntime()
    launcher.shader_runtime = ServiceRuntime()

    launcher._active_primary_config = None
    launcher._active_contain_config = None
    launcher._active_cheat_config = None

    archive_cache = (
        tmp_path
        / "archive-runtime"
        / "cached"
        / "Game.rom"
    )

    archive_cache.parent.mkdir(
        parents=True
    )

    archive_cache.write_bytes(
        b"RETROVAULT-CACHE"
    )

    launcher._cleanup_active_transients()

    assert archive_cache.is_file()

    assert archive_cache.read_bytes() == (
        b"RETROVAULT-CACHE"
    )


def test_a3n5e_all_post_primary_failure_paths_route_through_universal_cleanup():
    import ast
    from pathlib import Path

    launcher_path = (
        Path(__file__).resolve().parents[1]
        / "services"
        / "retroarch"
        / "launcher.py"
    )

    source = launcher_path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    launcher = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "RetroArchLauncher"
    )

    launch = next(
        node
        for node in launcher.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "launch"
    )

    def call_name(call):
        if not isinstance(call, ast.Call):
            return None

        func = call.func

        if isinstance(func, ast.Attribute):
            parts = [func.attr]
            value = func.value

            while isinstance(value, ast.Attribute):
                parts.append(value.attr)
                value = value.value

            if isinstance(value, ast.Name):
                parts.append(value.id)

            return ".".join(
                reversed(parts)
            )

        return None

    def contains_cleanup(node):
        return any(
            isinstance(child, ast.Call)
            and call_name(child)
            == "self._cleanup_active_transients"
            for child in ast.walk(node)
        )

    def contains_failure_return(node):
        for child in ast.walk(node):
            if not isinstance(child, ast.Return):
                continue

            if not isinstance(
                child.value,
                ast.Dict,
            ):
                continue

            for key, value in zip(
                child.value.keys,
                child.value.values,
            ):
                if (
                    isinstance(key, ast.Constant)
                    and key.value == "success"
                    and isinstance(value, ast.Constant)
                    and value.value is False
                ):
                    return True

        return False

    primary_line = min(
        child.lineno
        for child in ast.walk(launch)
        if isinstance(child, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "primary_config"
            for target in child.targets
        )
    )

    handlers = [
        node
        for node in ast.walk(launch)
        if isinstance(node, ast.ExceptHandler)
        and node.lineno > primary_line
        and contains_failure_return(node)
    ]

    assert len(handlers) == 7

    assert all(
        contains_cleanup(node)
        for node in handlers
    )


def test_a4c_loaded_core_display_aspect_supersedes_launch_profile_hint_before_contain(
    monkeypatch,
):
    """
    Final presentation geometry must follow the display aspect reported
    after real content is loaded, not a pre-launch LaunchProfile hint.

    The hint remains useful as fallback metadata, but it must not prevent
    the content-loaded core from supplying authoritative runtime geometry.
    """
    from models.launch_profile import LaunchProfile
    from services.retroarch.launcher import RetroArchLauncher

    runtime_aspect = 8 / 7
    probe = A7ContentLoadedDisplayAspectProbe(
        ratio=runtime_aspect
    )
    contain = A7StartupContainRuntime()

    class ArchiveRuntime:
        def resolve(
            self,
            rom,
            member=None,
        ):
            return rom

    class CoreOptions:
        def create(
            self,
            core,
            platform_id=None,
        ):
            return None

    class SessionConfig:
        def create(
            self,
            core_options_path=None,
            shader_enabled=False,
        ):
            return None

    class Process:
        pid = 99999999
        pid = 43210

        def poll(self):
            return None

    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        lambda *args, **kwargs: Process(),
    )

    launcher = RetroArchLauncher(
        executable="/custom/retroarch",
        display_aspect_probe=A7StartupDisplayAspectProbe(),
        content_display_aspect_probe=probe,
        contain_runtime=contain,
        archive_runtime=ArchiveRuntime(),
        core_options_runtime=CoreOptions(),
        session_config=SessionConfig(),
    )

    profile = LaunchProfile(
        game="Generic Runtime Aspect Authority",
        rom="/roms/runtime-authority.nes",
        core="/cores/fceumm_libretro.so",
        platform_id="platform.nintendo.nes",
        display_aspect_width=4.0,
        display_aspect_height=3.0,
    )

    result = launcher.launch(profile)

    assert result["success"] is True

    assert result["command"][0] == "/custom/retroarch"
    assert probe.calls[0]["command"] == "/custom/retroarch"
    assert len(probe.calls) == 1

    assert len(contain.calls) == 1

    resolved = contain.calls[0]["display_aspect"]

    assert resolved.width == runtime_aspect
    assert resolved.height == 1.0
    assert resolved.ratio == runtime_aspect


def test_production_layers_reach_retroarch_as_one_ordered_argument(tmp_path, monkeypatch):
    from pathlib import Path
    from services.retroarch.session_config import RetroArchSessionConfig
    from services.retroarch.core_options_runtime import CoreOptionsRuntimeConfig
    from services.retroarch.overlay_runtime import OverlayRuntimeConfig
    from services.retroarch.shader_runtime import ShaderRuntimeConfig
    from services.retroarch.contain_runtime import ContainRuntimeConfig

    from services.presentation.production_package import ProductionPresentationPackage
    from services.retroarch.adaptive_bezel_runtime import AdaptiveBezelRuntime
    root = Path(__file__).resolve().parents[1] / "retrovault/nes/classic"
    base = root / "RetroVault_NES_Classic"
    package = ProductionPresentationPackage(
        platform_id="platform.nintendo.nes",
        overlay=str(base.with_suffix(".cfg")),
        shader=str(root / "RetroVault_NES_Classic_CRT.slangp"),
        runtime_descriptor=str(base.with_suffix(".runtime.cfg")),
        production_manifest=str(base.with_suffix(".production.json")),
    )
    monkeypatch.setattr(
        "services.retroarch.launcher.CanonicalProductionPackageResolver.resolve",
        lambda **kwargs: package,
    )
    cheat = tmp_path / "cheats.cfg"
    cheat.write_text('cheevos_enable = "false"\n')
    archive = Mock()
    archive.resolve.return_value = "/roms/game.nes"
    cheats = Mock()
    cheats.create.return_value = str(cheat)
    probe = A7ContentLoadedDisplayAspectProbe(ratio=1.219)
    process = Mock()
    process.poll.return_value = None
    monkeypatch.setattr(
        "services.retroarch.launcher.subprocess.Popen",
        lambda *args, **kwargs: process,
    )
    launcher = RetroArchLauncher(
        primary_config_runtime=FakePrimaryConfigRuntime(),
        archive_runtime=archive,
        cheat_runtime=cheats,
        core_options_runtime=CoreOptionsRuntimeConfig(tmp_path),
        session_config=RetroArchSessionConfig(tmp_path),
        overlay_runtime=OverlayRuntimeConfig(tmp_path),
        shader_runtime=ShaderRuntimeConfig(tmp_path),
        contain_runtime=ContainRuntimeConfig(tmp_path),
        adaptive_bezel_runtime=AdaptiveBezelRuntime(tmp_path),
        content_display_aspect_probe=probe,
    )
    result = launcher.launch(LaunchProfile(
        game="Layer authority", rom="/roms/game.nes",
        core="/cores/fceumm_libretro.so",
        platform_id="platform.nintendo.nes", cheat_file="/cheats/game.cht",
    ))
    assert result["success"], result
    command = result["command"]
    assert command.count("--appendconfig") == 1
    layers = command[command.index("--appendconfig") + 1].split("|")
    assert len(layers) == 4
    assert layers[2] == str(cheat)
    assert probe.calls[0]["append_configs"][0] == layers[0]
    assert probe.calls[0]["append_configs"][1] != layers[1]
    assert package.overlay in Path(probe.calls[0]["append_configs"][1]).read_text()
    fitted = launcher.adaptive_bezel_runtime._created[0]
    assert str(fitted / "overlay.cfg") in Path(layers[1]).read_text()
    from PyQt6.QtGui import QImage
    artwork = QImage(str(fitted / "artwork.png"))
    assert artwork.pixelColor(493, 100).alpha() == 0
    assert artwork.pixelColor(492, 100).alpha() == 255
    assert artwork.pixelColor(1421, 861).alpha() == 0
    assert artwork.pixelColor(1422, 861).alpha() == 255
    session, overlay, _, contain = [Path(p).read_text() for p in layers]
    assert 'core_options_path = "' in session
    assert 'video_shader_enable = "true"' in session
    assert 'input_overlay_enable = "true"' in overlay
    assert 'custom_viewport_x = "493"' in contain
    assert 'custom_viewport_y = "100"' in contain
    assert 'custom_viewport_width = "929"' in contain
    assert 'custom_viewport_height = "762"' in contain
    assert 'video_viewport_bias_x = "0.000000"' in contain
    assert 'video_viewport_bias_y = "0.000000"' in contain
    assert Path(command[command.index("--set-shader") + 1]).is_file()


def test_explicit_primary_is_copied_once_and_cleaned_after_exit(tmp_path, monkeypatch):
    from pathlib import Path
    from services.retroarch.primary_config_runtime import PrimaryConfigRuntime
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    source = tmp_path / "user.cfg"
    source.write_text('video_driver = "vulkan"\nauto_overrides_enable = "true"\n')
    original = source.read_bytes()
    runtime = PrimaryConfigRuntime(tmp_path / "runtime")
    launcher = RetroArchLauncher(
        executable="/configured/retroarch",
        primary_config_runtime=runtime,
        session_config=FakeSessionConfig(),
    )
    profile = LaunchProfile("Example", "/roms/example.rom", "/cores/example.so", config=str(source))
    process = Mock()
    process.poll.return_value = None
    with patch("services.retroarch.launcher.subprocess.Popen", return_value=process) as popen:
        result = launcher.launch(profile)
    assert result["success"]
    command = popen.call_args.args[0]
    assert command[0] == "/configured/retroarch"
    assert command.count("--config") == 1
    copied = Path(command[command.index("--config") + 1])
    assert copied != source
    assert 'auto_overrides_enable = "false"' in copied.read_text()
    assert 'video_driver = "vulkan"' in copied.read_text()
    assert source.read_bytes() == original
    process.poll.return_value = 0
    launcher.clear_exited_process()
    assert not copied.exists()
    assert source.read_bytes() == original


def test_explicit_primary_cannot_fall_back_to_unisolated_config():
    class UnavailablePrimaryRuntime:
        def create(self, *, source=None, overlay=None):
            assert source == "/user/retroarch.cfg"
            return None

    launcher = RetroArchLauncher(
        primary_config_runtime=UnavailablePrimaryRuntime(),
        session_config=FakeSessionConfig(),
    )
    profile = LaunchProfile(
        "Example", "/roms/example.rom", "/cores/example.so",
        config="/user/retroarch.cfg",
    )
    with patch("services.retroarch.launcher.subprocess.Popen") as popen:
        result = launcher.launch(profile)
    assert result == {
        "success": False,
        "error": "Explicit primary configuration was not isolated.",
    }
    popen.assert_not_called()
    assert launcher.active_process is None


import pytest


@pytest.fixture(autouse=True)
def _valid_files_for_runtime_composition_tests(monkeypatch):
    """These tests isolate composition/process behavior; readiness has real-file tests."""
    from services.retroarch.validator import LaunchValidator
    monkeypatch.setattr(LaunchValidator, "check_retroarch", lambda self: True)
    monkeypatch.setattr(LaunchValidator, "check_core", lambda self: True)
    monkeypatch.setattr(LaunchValidator, "check_rom", lambda self, rom: True)


def test_launcher_uses_one_fresh_config_and_explicit_primary_precedence():
    primary = Mock()
    primary.create.return_value = '/runtime/primary.cfg'
    provider = Mock(return_value={'retroarch': {'primary_config': '/configured.cfg'}})
    launcher = RetroArchLauncher(primary_config_runtime=primary,
                                 session_config=FakeSessionConfig(),
                                 presentation_config_provider=provider)
    profile = LaunchProfile(game='fixture', rom='/roms/test.nes', core='/cores/fceumm_libretro.so')
    with patch('services.retroarch.launcher.subprocess.Popen') as popen:
        popen.return_value.poll.return_value = None
        assert launcher.launch(profile)['success']
    provider.assert_called_once()
    assert primary.create.call_args.kwargs['source'] == '/configured.cfg'
    launcher._active_process = None
    launcher._active_group = None
    profile.config = '/explicit.cfg'
    with patch('services.retroarch.launcher.subprocess.Popen') as popen:
        popen.return_value.poll.return_value = None
        assert launcher.launch(profile)['success']
    assert primary.create.call_args.kwargs['source'] == '/explicit.cfg'
    assert provider.call_count == 2
    launcher._active_process = None
    launcher._active_group = None


def test_direct_launch_rejects_tuning_without_package_before_extraction():
    archive=Mock()
    launcher=RetroArchLauncher(archive_runtime=archive)
    profile=LaunchProfile(game='Game',rom='/game.nes',core='/core.so',
                          visual_tuning=(('brightness',1.2),))
    result=launcher.launch(profile)
    assert not result['success']
    assert 'production package' in result['error']
    archive.resolve.assert_not_called()


def test_tuning_matches_probe_and_final_shader_without_geometry_override():
    runtime=FakeShaderRuntime(parameters={'HSM_NON_INTEGER_SCALE':'100.0'})
    probe=A7ContentLoadedDisplayAspectProbe()
    launcher=RetroArchLauncher(shader_runtime=runtime,
        display_aspect_probe=A7StartupDisplayAspectProbe(), content_display_aspect_probe=probe,
        contain_runtime=A7StartupContainRuntime(),primary_config_runtime=FakePrimaryConfigRuntime(),
        session_config=FakeSessionConfig())
    profile=LaunchProfile(game='Game',rom='/game.nes',core='/cores/fceumm_libretro.so',
        platform_id='platform.nintendo.nes',visual_tuning=(('brightness',1.25),))
    with patch('services.retroarch.launcher.subprocess.Popen') as popen:
        popen.return_value.poll.return_value=None
        result=launcher.launch(profile)
    assert result['success'],result
    assert len(runtime.resolve_calls)==2
    assert runtime.resolve_calls[0]==runtime.resolve_calls[1]
    assert runtime.resolve_calls[0][1]=={'HSM_NON_INTEGER_SCALE':'100.0','post_br':'1.25'}
    assert probe.calls[0]['shader']==runtime.runtime_shader
    assert result['command'][result['command'].index('--set-shader')+1]==runtime.runtime_shader
    launcher._active_process=None
    launcher._active_group=None
