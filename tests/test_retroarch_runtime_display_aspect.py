from pathlib import Path

import pytest

from services.retroarch.display_aspect import (
    CoreDisplayAspect,
)
from services.retroarch.runtime_display_aspect import (
    RuntimeDisplayAspectObserver,
)


def _ratio(aspect):
    assert isinstance(
        aspect,
        CoreDisplayAspect,
    )

    return aspect.width / aspect.height


def test_observer_starts_without_runtime_authority(
    tmp_path,
):
    observer = RuntimeDisplayAspectObserver(
        tmp_path / "retroarch.log"
    )

    assert observer.display_aspect is None
    assert observer.initial_geometry_seen is False
    assert observer.set_geometry_count == 0


def test_missing_log_is_nonblocking_noop(
    tmp_path,
):
    observer = RuntimeDisplayAspectObserver(
        tmp_path / "missing.log"
    )

    assert observer.poll() is None
    assert observer.display_aspect is None


def test_initial_core_geometry_establishes_display_aspect(
    tmp_path,
):
    log = tmp_path / "retroarch.log"

    log.write_text(
        "[INFO] [Core] Geometry: 256x224, "
        "Aspect: 1.306, FPS: 60.10, "
        "Sample rate: 48000.00 Hz.\n",
        encoding="utf-8",
    )

    observer = RuntimeDisplayAspectObserver(
        log
    )

    aspect = observer.poll()

    assert _ratio(aspect) == pytest.approx(
        1.306
    )
    assert observer.initial_geometry_seen is True
    assert observer.set_geometry_count == 0


def test_core_reported_aspect_overrides_raw_raster_ratio(
    tmp_path,
):
    log = tmp_path / "retroarch.log"

    log.write_text(
        "[INFO] [Core] Geometry: 256x224, "
        "Aspect: 1.306, FPS: 60.10, "
        "Sample rate: 48000.00 Hz.\n",
        encoding="utf-8",
    )

    aspect = RuntimeDisplayAspectObserver(
        log
    ).poll()

    assert _ratio(aspect) == pytest.approx(
        1.306
    )
    assert _ratio(aspect) != pytest.approx(
        256 / 224
    )


def test_nonpositive_reported_aspect_uses_libretro_raster_fallback(
    tmp_path,
):
    log = tmp_path / "retroarch.log"

    log.write_text(
        "[INFO] [Core] Geometry: 320x240, "
        "Aspect: 0.000.\n",
        encoding="utf-8",
    )

    aspect = RuntimeDisplayAspectObserver(
        log
    ).poll()

    assert _ratio(aspect) == pytest.approx(
        320 / 240
    )


def test_runtime_set_geometry_supersedes_initial_geometry(
    tmp_path,
):
    log = tmp_path / "retroarch.log"

    log.write_text(
        "\n".join(
            (
                "[INFO] [Core] Geometry: "
                "256x192, Aspect: 1.524, "
                "FPS: 59.92, Sample rate: "
                "44100.00 Hz.",
                "[INFO] [Environ] "
                "SET_GEOMETRY: 320x224, "
                "Aspect: 1.306.",
                "",
            )
        ),
        encoding="utf-8",
    )

    observer = RuntimeDisplayAspectObserver(
        log
    )

    aspect = observer.poll()

    assert _ratio(aspect) == pytest.approx(
        1.306
    )
    assert observer.initial_geometry_seen is True
    assert observer.set_geometry_count == 1


def test_latest_valid_set_geometry_wins(
    tmp_path,
):
    log = tmp_path / "retroarch.log"

    log.write_text(
        "\n".join(
            (
                "[INFO] [Core] Geometry: "
                "256x192, Aspect: 1.524.",
                "[INFO] [Environ] "
                "SET_GEOMETRY: 320x224, "
                "Aspect: 1.306.",
                "[INFO] [Environ] "
                "SET_GEOMETRY: 640x480, "
                "Aspect: 1.333333.",
                "",
            )
        ),
        encoding="utf-8",
    )

    observer = RuntimeDisplayAspectObserver(
        log
    )

    aspect = observer.poll()

    assert _ratio(aspect) == pytest.approx(
        1.333333
    )
    assert observer.set_geometry_count == 2


def test_repeated_core_geometry_cannot_roll_back_runtime_authority(
    tmp_path,
):
    log = tmp_path / "retroarch.log"

    log.write_text(
        "\n".join(
            (
                "[INFO] [Core] Geometry: "
                "256x192, Aspect: 1.524.",
                "[INFO] [Environ] "
                "SET_GEOMETRY: 320x224, "
                "Aspect: 1.306.",
                "[INFO] [Core] Geometry: "
                "256x192, Aspect: 1.524.",
                "",
            )
        ),
        encoding="utf-8",
    )

    observer = RuntimeDisplayAspectObserver(
        log
    )

    aspect = observer.poll()

    assert _ratio(aspect) == pytest.approx(
        1.306
    )
    assert observer.set_geometry_count == 1


def test_poll_reads_only_newly_appended_evidence(
    tmp_path,
):
    log = tmp_path / "retroarch.log"

    log.write_text(
        "[INFO] [Core] Geometry: "
        "256x192, Aspect: 1.524.\n",
        encoding="utf-8",
    )

    observer = RuntimeDisplayAspectObserver(
        log
    )

    first = observer.poll()

    assert _ratio(first) == pytest.approx(
        1.524
    )
    assert observer.set_geometry_count == 0

    with log.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            "[INFO] [Environ] "
            "SET_GEOMETRY: 320x224, "
            "Aspect: 1.306.\n"
        )

    second = observer.poll()

    assert _ratio(second) == pytest.approx(
        1.306
    )
    assert observer.set_geometry_count == 1

    third = observer.poll()

    assert third == second
    assert observer.set_geometry_count == 1


def test_partial_line_is_not_consumed_until_complete(
    tmp_path,
):
    log = tmp_path / "retroarch.log"

    log.write_text(
        "[INFO] [Core] Geometry: "
        "256x224, Aspect:",
        encoding="utf-8",
    )

    observer = RuntimeDisplayAspectObserver(
        log
    )

    assert observer.poll() is None

    with log.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            " 1.306, FPS: 60.10.\n"
        )

    aspect = observer.poll()

    assert _ratio(aspect) == pytest.approx(
        1.306
    )


def test_malformed_geometry_does_not_replace_valid_authority(
    tmp_path,
):
    log = tmp_path / "retroarch.log"

    log.write_text(
        "\n".join(
            (
                "[INFO] [Core] Geometry: "
                "256x224, Aspect: 1.306.",
                "[INFO] [Environ] "
                "SET_GEOMETRY: garbage.",
                "",
            )
        ),
        encoding="utf-8",
    )

    observer = RuntimeDisplayAspectObserver(
        log
    )

    aspect = observer.poll()

    assert _ratio(aspect) == pytest.approx(
        1.306
    )
    assert observer.set_geometry_count == 0


def test_invalid_dimensions_are_ignored(
    tmp_path,
):
    observer = RuntimeDisplayAspectObserver(
        tmp_path / "retroarch.log"
    )

    observer.observe_text(
        "[INFO] [Core] Geometry: "
        "0x224, Aspect: 1.306.\n"
    )

    assert observer.display_aspect is None
    assert observer.initial_geometry_seen is False


def test_log_truncation_restarts_observation(
    tmp_path,
):
    log = tmp_path / "retroarch.log"

    log.write_text(
        "\n".join(
            (
                "[INFO] [Core] Geometry: "
                "256x192, Aspect: 1.524.",
                "[INFO] [Environ] "
                "SET_GEOMETRY: 320x224, "
                "Aspect: 1.306.",
                "",
            )
        ),
        encoding="utf-8",
    )

    observer = RuntimeDisplayAspectObserver(
        log
    )

    assert _ratio(
        observer.poll()
    ) == pytest.approx(
        1.306
    )

    log.write_text(
        "[INFO] [Core] Geometry: "
        "256x224, Aspect: 1.333333.\n",
        encoding="utf-8",
    )

    aspect = observer.poll()

    assert _ratio(aspect) == pytest.approx(
        1.333333
    )
    assert observer.set_geometry_count == 0


def test_observer_accepts_real_nes_log_shape(
    tmp_path,
):
    log = tmp_path / "retroarch.log"

    log.write_text(
        "[INFO] [Core] Geometry: 256x224, "
        "Aspect: 1.306, FPS: 60.10, "
        "Sample rate: 48000.00 Hz.\n",
        encoding="utf-8",
    )

    observer = RuntimeDisplayAspectObserver(
        log
    )

    aspect = observer.poll()

    assert _ratio(aspect) == pytest.approx(
        1.306
    )
    assert observer.set_geometry_count == 0


def test_observer_accepts_real_genesis_transition_shape(
    tmp_path,
):
    log = tmp_path / "retroarch.log"

    log.write_text(
        "\n".join(
            (
                "[INFO] [Core] Geometry: "
                "256x192, Aspect: 1.524, "
                "FPS: 59.92, Sample rate: "
                "44100.00 Hz.",
                "[INFO] [Environ] "
                "SET_GEOMETRY: 320x224, "
                "Aspect: 1.306.",
                "",
            )
        ),
        encoding="utf-8",
    )

    observer = RuntimeDisplayAspectObserver(
        log
    )

    aspect = observer.poll()

    assert _ratio(aspect) == pytest.approx(
        1.306
    )
    assert observer.set_geometry_count == 1


def test_observer_contract_contains_no_content_identity():
    source = Path(
        "services/retroarch/"
        "runtime_display_aspect.py"
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


def test_observer_does_not_own_process_io():
    source = Path(
        "services/retroarch/"
        "runtime_display_aspect.py"
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
