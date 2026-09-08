import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SPEC = (
    ROOT
    / "data"
    / "presentation"
    / "specifications"
    / "rvv_nes_classic.json"
)


def load_spec():
    return json.loads(
        SPEC.read_text(encoding="utf-8")
    )


def test_native_nes_specification_exists():
    assert SPEC.is_file()


def test_native_nes_identity_matches_visual_catalog_contract():
    data = load_spec()

    assert data["version"] == 1
    assert data["id"] == "rvv.overlay.nes.classic"
    assert data["display_name"] == (
        "Nintendo NES — RetroVault Classic"
    )
    assert data["platform_id"] == (
        "platform.nintendo.nes"
    )
    assert data["asset_type"] == "overlay"
    assert data["source"] == "rvv_native"
    assert data["author"] == "RetroVault"


def test_native_nes_visual_is_declared_original():
    data = load_spec()

    originality = data["design"]["originality"]

    assert "original RetroVault" in originality
    assert "third-party bezel artwork" in originality
    assert "Nintendo artwork" in originality


def test_native_nes_runtime_contract():
    runtime = load_spec()["design"]["runtime"]

    assert runtime["target_aspect"] == "16:9"
    assert runtime["game_aspect"] == "4:3"
    assert runtime["target_resolution"] == "1920x1080"
    assert runtime["overlay_format"] == "PNG"
    assert runtime["descriptor_format"] == (
        "RetroArch overlay CFG"
    )
    assert runtime["shader_independent"] is True
    assert runtime["shader_compatible"] is True


def test_native_nes_catalog_reference_is_portable():
    data = load_spec()

    assert data["catalog"]["reference"] == (
        "retro-vault://overlays/"
        "retrovault/nes/classic/"
        "RetroVault_NES_Classic.cfg"
    )


def test_native_nes_production_paths_are_relative():
    assets = load_spec()["production_assets"]

    for value in assets.values():
        path = Path(value)

        assert not path.is_absolute()
        assert ".." not in path.parts


def test_native_nes_specification_is_not_yet_production_asset():
    data = load_spec()

    assert data["production_status"] == "specified"
