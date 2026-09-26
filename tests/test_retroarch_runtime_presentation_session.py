from pathlib import Path

import pytest

from services.presentation.master_profile import (
    MasterPresentationClass,
    MasterPresentationProfile,
)
from services.retroarch.runtime_presentation_session import (
    RuntimePresentationSession,
)


def _nes_glass():
    return MasterPresentationProfile(
        profile_class=(
            MasterPresentationClass.CLASSIC_4_3
        ),
        canvas_width=1920,
        canvas_height=1080,
        envelope_x=355,
        envelope_y=100,
        envelope_width=1206,
        envelope_height=762,
    )


def _read_config(path):
    values = {}

    for raw in Path(path).read_text(
        encoding="utf-8",
    ).splitlines():
        line = raw.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split(
            "=",
            1,
        )

        values[key.strip()] = (
            value.strip().strip('"')
        )

    return values


def test_session_creates_isolated_log(
    tmp_path,
):
    session = RuntimePresentationSession(
        _nes_glass(),
        directory=tmp_path,
    )

    first = session.create()

    assert Path(first).parent.parent == tmp_path
    assert Path(first).name == "retroarch.log"

    session.cleanup()

    second = session.create()

    assert second != first

    session.cleanup()


def test_session_rejects_double_create(
    tmp_path,
):
    session = RuntimePresentationSession(
        _nes_glass(),
        directory=tmp_path,
    )

    session.create()

    with pytest.raises(
        RuntimeError,
        match="already active",
    ):
        session.create()

    session.cleanup()


def test_nes_runtime_aspect_generates_contained_viewport(
    tmp_path,
):
    session = RuntimePresentationSession(
        _nes_glass(),
        directory=tmp_path,
    )

    log_path = Path(
        session.create()
    )

    log_path.write_text(
        "[INFO] [Core] Geometry: "
        "256x224, Aspect: 1.306, "
        "FPS: 60.10, Sample rate: "
        "48000.00 Hz.\n",
        encoding="utf-8",
    )

    contain_path = session.poll()

    assert contain_path is not None

    values = _read_config(
        contain_path
    )

    assert values[
        "custom_viewport_x"
    ] == "460"

    assert values[
        "custom_viewport_y"
    ] == "100"

    assert values[
        "custom_viewport_width"
    ] == "995"

    assert values[
        "custom_viewport_height"
    ] == "762"

    session.cleanup()


def test_set_geometry_replaces_previous_contain_authority(
    tmp_path,
):
    session = RuntimePresentationSession(
        _nes_glass(),
        directory=tmp_path,
    )

    log_path = Path(
        session.create()
    )

    log_path.write_text(
        "[INFO] [Core] Geometry: "
        "256x192, Aspect: 1.524.\n",
        encoding="utf-8",
    )

    first = session.poll()

    assert first is not None

    first_values = _read_config(
        first
    )

    with log_path.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            "[INFO] [Environ] "
            "SET_GEOMETRY: 320x224, "
            "Aspect: 1.306.\n"
        )

    second = session.poll()

    assert second is not None

    second_values = _read_config(
        second
    )

    assert first_values != second_values

    assert second_values[
        "custom_viewport_x"
    ] == "460"

    assert second_values[
        "custom_viewport_y"
    ] == "100"

    assert second_values[
        "custom_viewport_width"
    ] == "995"

    assert second_values[
        "custom_viewport_height"
    ] == "762"

    assert (
        session.observer.set_geometry_count
        == 1
    )

    session.cleanup()


def test_unchanged_aspect_reuses_contain_descriptor(
    tmp_path,
):
    session = RuntimePresentationSession(
        _nes_glass(),
        directory=tmp_path,
    )

    log_path = Path(
        session.create()
    )

    log_path.write_text(
        "[INFO] [Core] Geometry: "
        "256x224, Aspect: 1.306.\n",
        encoding="utf-8",
    )

    first = session.poll()
    second = session.poll()

    assert first == second

    session.cleanup()


def test_missing_runtime_evidence_creates_no_viewport(
    tmp_path,
):
    session = RuntimePresentationSession(
        _nes_glass(),
        directory=tmp_path,
    )

    session.create()

    assert session.poll() is None
    assert session.contain_path is None

    session.cleanup()


def test_cleanup_removes_session_and_contain_files(
    tmp_path,
):
    session = RuntimePresentationSession(
        _nes_glass(),
        directory=tmp_path,
    )

    log_path = Path(
        session.create()
    )

    log_path.write_text(
        "[INFO] [Core] Geometry: "
        "256x224, Aspect: 1.306.\n",
        encoding="utf-8",
    )

    contain_path = Path(
        session.poll()
    )

    session_directory = (
        log_path.parent
    )

    assert session_directory.exists()
    assert contain_path.exists()

    session.cleanup()

    assert not session_directory.exists()
    assert not contain_path.exists()
    assert session.log_path is None
    assert session.contain_path is None


def test_fixed_glass_profile_is_not_mutated(
    tmp_path,
):
    profile = _nes_glass()

    before = (
        profile.envelope_x,
        profile.envelope_y,
        profile.envelope_width,
        profile.envelope_height,
    )

    session = RuntimePresentationSession(
        profile,
        directory=tmp_path,
    )

    log_path = Path(
        session.create()
    )

    log_path.write_text(
        "[INFO] [Core] Geometry: "
        "256x224, Aspect: 1.306.\n",
        encoding="utf-8",
    )

    session.poll()

    after = (
        profile.envelope_x,
        profile.envelope_y,
        profile.envelope_width,
        profile.envelope_height,
    )

    assert after == before

    session.cleanup()


def test_session_contract_contains_no_content_identity():
    source = Path(
        "services/retroarch/"
        "runtime_presentation_session.py"
    ).read_text(
        encoding="utf-8",
    ).lower()

    forbidden = (
        "duck tales",
        "ducktales",
        "sonic the hedgehog",
        "street fighter",
        "rom_path",
        "game_id",
        "archive_member",
        "title_screen",
        "gameplay_state",
    )

    for token in forbidden:
        assert token not in source


def test_session_does_not_own_process_io():
    source = Path(
        "services/retroarch/"
        "runtime_presentation_session.py"
    ).read_text(
        encoding="utf-8",
    )

    forbidden = (
        "subprocess.Popen",
        "subprocess.PIPE",
        ".communicate(",
        ".wait(",
        ".stdout",
        ".stderr",
    )

    for token in forbidden:
        assert token not in source
