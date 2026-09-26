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


class FakePrimaryConfigRuntime:
    """
    Preserve historical launcher command expectations in tests that are
    not specifically exercising early primary-config runtime authority.

    Dedicated tests inject their own PrimaryRuntime and verify the new
    production --config contract explicitly.
    """

    def create(self, *, overlay=None):
        return None


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
        ):
            return None

    class Process:
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
        ):
            return None

    class Process:
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
        ):
            return None

    class Process:
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
        ):
            return None

    class Process:
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
        ):
            return None

    class Process:
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


def test_a3n3b4_unconfigured_cannot_borrow_ready_package_before_archive(
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
    assert "not configured" in result["error"]
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
        ):
            return "/runtime/session.cfg"

    class Process:
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


def test_launchprofile_config_preserves_existing_config_semantics_with_primary_runtime(
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
        ):
            return "/runtime/session.cfg"

    class Process:
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

    # Preserve the launcher's pre-existing LaunchProfile.config
    # contract. It remains --config; this repair must not silently
    # reinterpret it as --appendconfig.
    assert [
        "--config",
        "/user/extra.cfg",
    ] == command[
        command.index(
            "/user/extra.cfg"
        ) - 1:
        command.index(
            "/user/extra.cfg"
        ) + 1
    ]

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
