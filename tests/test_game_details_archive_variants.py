from unittest.mock import Mock

from PyQt6.QtWidgets import QApplication, QInputDialog

from services.library.models import Game
from ui.library.details.game_details import GameDetails


_APP = QApplication.instance()

if _APP is None:
    _APP = QApplication([])


def _game(rom):
    return Game(
        name="Variant Game",
        platform="Nintendo Entertainment System",
        year=1987,
        genre="Platform",
        core="fceumm_libretro.so",
        rom=rom,
        rvdb_platform_id="platform.nintendo.nes",
    )


def test_single_archive_member_launches_without_dialog(
    tmp_path,
    monkeypatch,
):
    archive = tmp_path / "Variant Game.7z"
    archive.write_bytes(b"archive")

    archive_runtime = Mock()
    archive_runtime.playable_members.return_value = [
        "Variant Game (U) [!].nes",
    ]

    details = GameDetails(
        archive_runtime=archive_runtime,
    )
    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        Mock(
            side_effect=AssertionError(
                "single-member archive must not show selector"
            )
        ),
    )

    selected = details._select_archive_member(
        str(archive)
    )

    assert selected == "Variant Game (U) [!].nes"
    archive_runtime.preferred_member.assert_not_called()


def test_multi_member_archive_preselects_preferred_variant(
    tmp_path,
    monkeypatch,
):
    archive = tmp_path / "Variant Game.7z"
    archive.write_bytes(b"archive")

    members = [
        "Variant Game (J).nes",
        "Variant Game (U) [!].nes",
        "Variant Game (U) [b1].nes",
    ]

    archive_runtime = Mock()
    archive_runtime.playable_members.return_value = members
    archive_runtime.preferred_from_members.return_value = (
        "Variant Game (U) [!].nes"
    )

    details = GameDetails(
        archive_runtime=archive_runtime,
    )
    dialog = Mock(
        return_value=(
            "Variant Game (J) — Japan",
            True,
        )
    )

    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        dialog,
    )

    selected = details._select_archive_member(
        str(archive)
    )

    assert selected == "Variant Game (J).nes"

    args = dialog.call_args.args

    assert args[1] == "Select Game Version"
    assert args[2] == "Choose the version to launch:"
    assert args[3] == [
        "Variant Game (J) — Japan",
        (
            "Variant Game (U) [!] — "
            "Recommended • USA • Verified"
        ),
        (
            "Variant Game (U) [b1] — "
            "USA • Bad Dump"
        ),
    ]
    assert args[4] == 1
    assert args[5] is False


def test_multi_member_archive_cancel_aborts_selection(
    tmp_path,
    monkeypatch,
):
    archive = tmp_path / "Variant Game.7z"
    archive.write_bytes(b"archive")

    archive_runtime = Mock()
    archive_runtime.playable_members.return_value = [
        "Variant Game (U) [!].nes",
        "Variant Game (J).nes",
    ]
    archive_runtime.preferred_from_members.return_value = (
        "Variant Game (U) [!].nes"
    )

    details = GameDetails(
        archive_runtime=archive_runtime,
    )
    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        Mock(
            return_value=(
                "Variant Game (U) [!].nes",
                False,
            )
        ),
    )

    assert (
        details._select_archive_member(
            str(archive)
        )
        is None
    )


def test_cancelled_archive_selector_does_not_start_lifecycle(
    tmp_path,
    monkeypatch,
):
    archive = tmp_path / "Variant Game.7z"
    archive.write_bytes(b"archive")

    archive_runtime = Mock()
    archive_runtime.playable_members.return_value = [
        "Variant Game (U) [!].nes",
        "Variant Game (J).nes",
    ]
    archive_runtime.preferred_from_members.return_value = (
        "Variant Game (U) [!].nes"
    )

    lifecycle = Mock()
    launcher = Mock()

    details = GameDetails(
        archive_runtime=archive_runtime,
        process_lifecycle=lifecycle,
        launcher=launcher,
    )
    details.current_game = _game(
        str(archive)
    )

    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        Mock(
            return_value=(
                "Variant Game (U) [!].nes",
                False,
            )
        ),
    )

    details.launch_game()

    lifecycle.launch_requested.assert_not_called()
    lifecycle.launch_failed.assert_not_called()
    lifecycle.launch_result.assert_not_called()
    launcher.launch.assert_not_called()


def test_selected_archive_variant_reaches_launch_profile(
    tmp_path,
    monkeypatch,
):
    archive = tmp_path / "Variant Game.7z"
    archive.write_bytes(b"archive")

    archive_runtime = Mock()
    archive_runtime.playable_members.return_value = [
        "Variant Game (U) [!].nes",
        "Variant Game (J).nes",
    ]
    archive_runtime.preferred_from_members.return_value = (
        "Variant Game (U) [!].nes"
    )

    launcher = Mock()
    launcher.launch.return_value = {
        "success": True,
        "command": [],
    }

    details = GameDetails(
        archive_runtime=archive_runtime,
        launcher=launcher,
    )
    details.current_game = _game(
        str(archive)
    )

    monkeypatch.setattr(
        details.core_resolver,
        "find",
        lambda _core: "/cores/fceumm_libretro.so",
    )

    class ReadyValidator:
        def __init__(self, *_args, **_kwargs):
            pass

        def validate(self, _rom):
            return {
                "retroarch": True,
                "core": True,
                "rom": True,
                "ready": True,
            }

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        ReadyValidator,
    )

    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        Mock(
            return_value=(
                "Variant Game (J) — Japan",
                True,
            )
        ),
    )

    details.launch_game()

    launcher.launch.assert_called_once()

    profile = launcher.launch.call_args.args[0]

    assert profile.rom == str(archive)
    assert profile.archive_member == "Variant Game (J).nes"
    assert profile.core == "/cores/fceumm_libretro.so"


def test_non_archive_launch_profile_has_no_archive_member(
    tmp_path,
    monkeypatch,
):
    rom = tmp_path / "Normal Game.nes"
    rom.write_bytes(b"rom")

    archive_runtime = Mock()
    launcher = Mock()
    launcher.launch.return_value = {
        "success": True,
        "command": [],
    }

    details = GameDetails(
        archive_runtime=archive_runtime,
        launcher=launcher,
    )
    details.current_game = _game(
        str(rom)
    )

    monkeypatch.setattr(
        details.core_resolver,
        "find",
        lambda _core: "/cores/fceumm_libretro.so",
    )

    class ReadyValidator:
        def __init__(self, *_args, **_kwargs):
            pass

        def validate(self, _rom):
            return {
                "retroarch": True,
                "core": True,
                "rom": True,
                "ready": True,
            }

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        ReadyValidator,
    )

    details.launch_game()

    archive_runtime.playable_members.assert_not_called()

    profile = launcher.launch.call_args.args[0]

    assert profile.archive_member == ""


def test_multi_member_selector_does_not_reinspect_archive(
    monkeypatch,
):
    members = [
        "Variant Game (J).nes",
        "Variant Game (U) [!].nes",
        "Variant Game (U) [b1].nes",
    ]

    runtime = Mock()
    runtime.playable_members.return_value = members
    runtime.preferred_from_members.return_value = (
        "Variant Game (U) [!].nes"
    )

    details = GameDetails(
        archive_runtime=runtime,
    )

    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        Mock(
            return_value=(
                "Variant Game (J) — Japan",
                True,
            )
        ),
    )

    selected = details._select_archive_member(
        "/library/Variant Game.7z"
    )

    assert selected == "Variant Game (J).nes"

    runtime.playable_members.assert_called_once_with(
        "/library/Variant Game.7z"
    )

    runtime.preferred_from_members.assert_called_once_with(
        "/library/Variant Game.7z",
        members,
    )

    runtime.preferred_member.assert_not_called()


def test_archive_inspection_failure_does_not_start_launch(
    monkeypatch,
):
    runtime = Mock()
    runtime.playable_members.side_effect = OSError(
        "archive inspection failed"
    )

    lifecycle = Mock()
    launcher = Mock()

    details = GameDetails(
        archive_runtime=runtime,
        process_lifecycle=lifecycle,
        launcher=launcher,
    )

    details.current_game = Mock(
        rom="/library/Broken Archive.7z",
        rvdb_platform_id="platform.nintendo.nes",
    )

    details.launch_game()

    lifecycle.launch_requested.assert_not_called()
    launcher.launch.assert_not_called()


def test_archive_selector_value_error_does_not_start_launch(
    monkeypatch,
):
    runtime = Mock()
    runtime.playable_members.side_effect = ValueError(
        "invalid archive member"
    )

    lifecycle = Mock()
    launcher = Mock()

    details = GameDetails(
        archive_runtime=runtime,
        process_lifecycle=lifecycle,
        launcher=launcher,
    )

    details.current_game = Mock(
        rom="/library/Unsafe Archive.7z",
        rvdb_platform_id="platform.nintendo.nes",
    )

    details.launch_game()

    lifecycle.launch_requested.assert_not_called()
    launcher.launch.assert_not_called()


def test_cancelled_variant_selector_does_not_start_launch(
    monkeypatch,
):
    members = [
        "Variant Game (J).nes",
        "Variant Game (U) [!].nes",
    ]

    runtime = Mock()
    runtime.playable_members.return_value = members
    runtime.preferred_from_members.return_value = (
        "Variant Game (U) [!].nes"
    )

    lifecycle = Mock()
    launcher = Mock()

    details = GameDetails(
        archive_runtime=runtime,
        process_lifecycle=lifecycle,
        launcher=launcher,
    )

    details.current_game = Mock(
        rom="/library/Variant Game.7z",
        rvdb_platform_id="platform.nintendo.nes",
    )

    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        Mock(
            return_value=(
                "",
                False,
            )
        ),
    )

    details.launch_game()

    lifecycle.launch_requested.assert_not_called()
    launcher.launch.assert_not_called()


def test_zero_playable_members_preserves_runtime_launch_path(
    monkeypatch,
):
    runtime = Mock()
    runtime.playable_members.return_value = []

    lifecycle = Mock()
    launcher = Mock()
    launcher.launch.return_value = {
        "success": False,
        "command": [],
    }

    details = GameDetails(
        archive_runtime=runtime,
        process_lifecycle=lifecycle,
        launcher=launcher,
    )

    details.current_game = Mock(
        name="Empty Archive",
        rom="/library/Empty Archive.7z",
        core="fceumm",
        rvdb_platform_id="platform.nintendo.nes",
    )

    monkeypatch.setattr(
        details.core_resolver,
        "find",
        Mock(
            return_value="/cores/fceumm_libretro.so"
        ),
    )

    class ReadyValidator:
        def __init__(self, *_args, **_kwargs):
            pass

        def validate(self, _rom):
            return {
                "retroarch": True,
                "core": True,
                "rom": True,
                "ready": True,
            }

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        ReadyValidator,
    )

    details.launch_game()

    runtime.playable_members.assert_called_once_with(
        "/library/Empty Archive.7z"
    )

    lifecycle.launch_requested.assert_called_once_with(
        "platform.nintendo.nes"
    )

    launcher.launch.assert_called_once()

    profile = launcher.launch.call_args.args[0]

    assert profile.archive_member == ""
    assert profile.rom == "/library/Empty Archive.7z"


def test_duplicate_display_labels_remain_individually_selectable(
    monkeypatch,
):
    members = [
        "set-a/Variant Game (U) [!].nes",
        "set-b/Variant Game (U) [!].nes",
    ]

    runtime = Mock()
    runtime.playable_members.return_value = members
    runtime.preferred_from_members.return_value = ""

    details = GameDetails(
        archive_runtime=runtime,
    )

    dialog = Mock(
        return_value=(
            (
                "Variant Game (U) [!] — "
                "USA • Verified [Variant 2]"
            ),
            True,
        )
    )

    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        dialog,
    )

    selected = details._select_archive_member(
        "/library/Variant Game.7z"
    )

    assert selected == members[1]

    args = dialog.call_args.args

    assert args[3] == [
        (
            "Variant Game (U) [!] — "
            "USA • Verified"
        ),
        (
            "Variant Game (U) [!] — "
            "USA • Verified [Variant 2]"
        ),
    ]

    assert len(args[3]) == len(
        set(args[3])
    )


def test_identical_nonpreferred_labels_receive_unique_suffix(
    monkeypatch,
):
    members = [
        "preferred/Variant Game (J) [!].nes",
        "set-a/Variant Game (U) [b1].nes",
        "set-b/Variant Game (U) [b1].nes",
    ]

    runtime = Mock()
    runtime.playable_members.return_value = members
    runtime.preferred_from_members.return_value = members[0]

    details = GameDetails(
        archive_runtime=runtime,
    )

    dialog = Mock(
        return_value=(
            (
                "Variant Game (U) [b1] — "
                "USA • Bad Dump [Variant 2]"
            ),
            True,
        )
    )

    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        dialog,
    )

    selected = details._select_archive_member(
        "/library/Variant Game.7z"
    )

    assert selected == members[2]

    labels = dialog.call_args.args[3]

    assert labels == [
        (
            "Variant Game (J) [!] — "
            "Recommended • Japan • Verified"
        ),
        (
            "Variant Game (U) [b1] — "
            "USA • Bad Dump"
        ),
        (
            "Variant Game (U) [b1] — "
            "USA • Bad Dump [Variant 2]"
        ),
    ]

    assert len(labels) == len(set(labels))
