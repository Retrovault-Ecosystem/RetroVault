import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SPEC = (
    ROOT
    / "data"
    / "presentation"
    / "specifications"
    / "rvv_snes_classic.json"
)


def load_spec():
    return json.loads(
        SPEC.read_text(encoding="utf-8")
    )


def test_native_snes_specification_exists():
    assert SPEC.is_file()


def test_native_snes_identity_contract():
    data = load_spec()

    assert data["version"] == 1
    assert data["id"] == "rvv.overlay.snes.classic"
    assert data["family"] == "RetroVault Classic"
    assert data["display_name"] == (
        "Nintendo SNES — RetroVault Classic"
    )
    assert data["platform_id"] == (
        "platform.nintendo.snes"
    )
    assert data["asset_type"] == "overlay"
    assert data["source"] == "rvv_native"
    assert data["author"] == "RetroVault"


def test_native_snes_visual_is_declared_original():
    originality = (
        load_spec()["design"]["originality"]
    )

    assert "original RetroVault" in originality
    assert "third-party bezel artwork" in originality
    assert "console photography" in originality
    assert "external pack artwork" in originality
    assert "third-party trademark" in originality
    assert (
        "ownership of those marks is not claimed"
        in originality
    )


def test_native_snes_runtime_family_contract():
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

    assert runtime["canvas"] == {
        "width": 1920,
        "height": 1080,
    }



def test_native_snes_geometry_contract():
    runtime = load_spec()["design"]["runtime"]
    viewport = runtime["game_viewport"]

    assert viewport["status"] == "accepted_geometry"

    assert (
        runtime["safe_zone"]["status"]
        == "design_pending"
    )

    assert viewport["x"] == 353
    assert viewport["y"] == 87
    assert viewport["width"] == 1216
    assert viewport["height"] == 750

def test_native_snes_is_not_prematurely_production():
    data = load_spec()

    assert data["production_status"] == "design"
    assert data["production_assets"] == {
        "status": "design_pending"
    }


def test_native_snes_planned_reference_is_portable():
    reference = (
        load_spec()["catalog"]["planned_reference"]
    )

    assert reference == (
        "retro-vault://overlays/"
        "retrovault/snes/classic/"
        "RetroVault_SNES_Classic.cfg"
    )


def test_native_snes_premium_family_contract():
    finish = load_spec()["design"]["finish"]

    assert (
        finish["quality_target"]
        == "premium showroom"
    )

    assert (
        "RetroVault Classic"
        in finish["consistency"]
    )

    assert (
        "early-1990s"
        in finish["consistency"]
    )


def test_native_snes_trademark_boundary():
    policy = load_spec()["trademark_policy"]

    assert (
        "not claimed as RetroVault intellectual property"
        in policy["platform_identity"]
    )

    assert (
        "must remain distinct"
        in policy["separation"]
    )



def test_native_snes_selected_master_visual_direction():
    data = load_spec()
    selection = data["design"]["master_visual_selection"]

    assert selection["status"] == "selected"

    assert (
        "RetroVault Classic"
        in selection["family_direction"]
    )

    assert (
        "NES master"
        in selection["housing"]["nes_relationship"]
    )

    assert (
        selection["gameplay_aperture"]["geometry_status"]
        == "accepted_geometry"
    )

    assert (
        selection["right_panel"]["controller_imagery"]
        == "excluded"
    )

    assert (
        selection["right_panel"]["joystick_imagery"]
        == "excluded"
    )

    assert (
        selection["right_panel"]["identity_element"]
        == "16-BIT"
    )

    assert (
        selection["lower_branding"]["retrovault_position"]
        == "centered above platform identity"
    )

    assert (
        selection["lower_branding"]
        ["platform_identity_position"]
        == "centered directly below RetroVault"
    )

    assert (
        "Super Nintendo Entertainment System"
        in selection["lower_branding"]
        ["selected_platform_mark"]
    )

    assert (
        selection["lower_branding"]["selection_status"]
        == "approved"
    )

    assert selection["controller"]["included"] is False


def test_native_snes_master_selection_does_not_promote_production():
    data = load_spec()

    assert data["production_status"] == "design"

    assert data["production_assets"] == {
        "status": "design_pending"
    }

    runtime = data["design"]["runtime"]

    assert (
        runtime["game_viewport"]["status"]
        == "accepted_geometry"
    )

    assert (
        runtime["safe_zone"]["status"]
        == "design_pending"
    )

def test_native_snes_selected_master_geometry():
    data = load_spec()
    runtime = data["design"]["runtime"]
    viewport = runtime["game_viewport"]

    assert viewport["status"] == "accepted_geometry"

    assert viewport["x"] == 353
    assert viewport["y"] == 87
    assert viewport["width"] == 1216
    assert viewport["height"] == 750

    assert viewport["normalized"] == {
        "x": 0.183854,
        "y": 0.080556,
        "width": 0.633333,
        "height": 0.694444,
    }

    derivation = viewport["derivation"]

    assert derivation["source"] == (
        "selected G.3 SNES master preview"
    )

    assert derivation["source_canvas"] == {
        "width": 1672,
        "height": 941,
    }

    assert derivation["measured_aperture"] == {
        "x": 307,
        "y": 76,
        "width": 1059,
        "height": 653,
    }

    assert derivation["target_canvas"] == {
        "width": 1920,
        "height": 1080,
    }


def test_native_snes_aperture_does_not_replace_game_aspect():
    data = load_spec()
    runtime = data["design"]["runtime"]

    assert runtime["game_aspect"] == "4:3"

    assert (
        "does not force"
        in runtime["game_viewport"]["policy"]
    )

    assert (
        "RetroArch"
        in runtime["game_viewport"]["policy"]
    )


def test_native_snes_master_selection_tracks_geometry():
    data = load_spec()

    aperture = (
        data["design"]
        ["master_visual_selection"]
        ["gameplay_aperture"]
    )

    assert (
        aperture["geometry_status"]
        == "accepted_geometry"
    )

    assert aperture["production_geometry"] == {
        "x": 353,
        "y": 87,
        "width": 1216,
        "height": 750,
    }


def test_native_snes_safe_zone_remains_unlocked():
    data = load_spec()
    runtime = data["design"]["runtime"]

    assert (
        runtime["safe_zone"]["status"]
        == "design_pending"
    )


def test_native_snes_geometry_does_not_promote_production():
    data = load_spec()

    assert data["production_status"] == "design"

    assert data["production_assets"] == {
        "status": "design_pending"
    }
