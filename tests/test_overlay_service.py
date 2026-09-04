from pathlib import Path

from services.overlays import (
    Overlay,
    OverlayService,
)


def write_overlay(
    path,
    *references,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = [
        f'overlay{index}_overlay = "{reference}"'
        for index, reference
        in enumerate(references)
    ]

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    return path


def test_missing_directory_returns_empty(
    tmp_path,
):
    service = OverlayService(
        tmp_path / "missing"
    )

    assert service.scan() == []


def test_empty_directory_returns_empty(
    tmp_path,
):
    service = OverlayService(
        tmp_path
    )

    assert service.scan() == []


def test_discovers_retroarch_cfg(
    tmp_path,
):
    config = write_overlay(
        tmp_path / "nes.cfg"
    )

    overlays = OverlayService(
        tmp_path
    ).scan()

    assert len(overlays) == 1
    assert isinstance(
        overlays[0],
        Overlay,
    )
    assert overlays[0].config_path == (
        config
    )
    assert overlays[0].relative_config == (
        Path("nes.cfg")
    )
    assert overlays[0].name == "nes"


def test_discovery_is_recursive(
    tmp_path,
):
    write_overlay(
        tmp_path
        / "Nintendo"
        / "NES"
        / "console.cfg"
    )

    overlays = OverlayService(
        tmp_path
    ).scan()

    assert [
        overlay.relative_config
        for overlay in overlays
    ] == [
        Path(
            "Nintendo/NES/console.cfg"
        )
    ]


def test_cfg_extension_is_case_insensitive(
    tmp_path,
):
    write_overlay(
        tmp_path / "Arcade.CFG"
    )

    assert len(
        OverlayService(
            tmp_path
        ).scan()
    ) == 1


def test_ignores_standalone_images_and_other_files(
    tmp_path,
):
    (
        tmp_path / "orphan.png"
    ).write_bytes(b"png")

    (
        tmp_path / "notes.txt"
    ).write_text(
        "not an overlay",
        encoding="utf-8",
    )

    assert OverlayService(
        tmp_path
    ).scan() == []


def test_resolves_relative_overlay_image(
    tmp_path,
):
    image = (
        tmp_path / "images" / "nes.png"
    )
    image.parent.mkdir()
    image.write_bytes(b"png")

    write_overlay(
        tmp_path / "nes.cfg",
        "images/nes.png",
    )

    overlay = OverlayService(
        tmp_path
    ).scan()[0]

    assert overlay.image_paths == (
        image.resolve(),
    )
    assert overlay.missing_images == ()
    assert overlay.ready is True
    assert overlay.image_count == 1


def test_reports_missing_referenced_image(
    tmp_path,
):
    missing = (
        tmp_path / "missing.png"
    ).resolve()

    write_overlay(
        tmp_path / "broken.cfg",
        "missing.png",
    )

    overlay = OverlayService(
        tmp_path
    ).scan()[0]

    assert overlay.image_paths == (
        missing,
    )
    assert overlay.missing_images == (
        missing,
    )
    assert overlay.ready is False


def test_duplicate_image_references_are_normalized(
    tmp_path,
):
    image = tmp_path / "same.png"
    image.write_bytes(b"png")

    write_overlay(
        tmp_path / "duplicate.cfg",
        "same.png",
        "same.png",
    )

    overlay = OverlayService(
        tmp_path
    ).scan()[0]

    assert overlay.image_paths == (
        image.resolve(),
    )


def test_non_image_overlay_value_is_ignored(
    tmp_path,
):
    write_overlay(
        tmp_path / "invalid.cfg",
        "not-an-image.txt",
    )

    overlay = OverlayService(
        tmp_path
    ).scan()[0]

    assert overlay.image_paths == ()
    assert overlay.ready is True


def test_non_overlay_config_keys_are_ignored(
    tmp_path,
):
    path = tmp_path / "settings.cfg"

    path.write_text(
        (
            'input_overlay = "wrong.png"\n'
            'overlay0_name = "wrong.png"\n'
        ),
        encoding="utf-8",
    )

    overlay = OverlayService(
        tmp_path
    ).scan()[0]

    assert overlay.image_paths == ()


def test_scan_order_is_deterministic(
    tmp_path,
):
    write_overlay(
        tmp_path / "zeta.cfg"
    )
    write_overlay(
        tmp_path / "Alpha.cfg"
    )
    write_overlay(
        tmp_path / "nested" / "beta.cfg"
    )

    overlays = OverlayService(
        tmp_path
    ).scan()

    assert [
        str(
            overlay.relative_config
        )
        for overlay in overlays
    ] == [
        "Alpha.cfg",
        "nested/beta.cfg",
        "zeta.cfg",
    ]


def test_display_name_normalizes_separators(
    tmp_path,
):
    write_overlay(
        tmp_path
        / "mega-bezel_arcade.cfg"
    )

    overlay = OverlayService(
        tmp_path
    ).scan()[0]

    assert overlay.name == (
        "mega bezel arcade"
    )
