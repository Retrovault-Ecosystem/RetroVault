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


def test_native_snes_legacy_geometry_is_preserved():
    runtime = load_spec()["design"]["runtime"]
    viewport = runtime["game_viewport"]

    assert (
        viewport["status"]
        == "superseded_by_production_alpha"
    )

    assert viewport["legacy_geometry"] == {
        "x": 353,
        "y": 87,
        "width": 1216,
        "height": 750,
    }

    assert (
        "fully transparent"
        in viewport["production_policy"]
    )

    assert (
        "feathered"
        in viewport["production_policy"]
    )


def test_native_snes_package_is_production_validated():
    data = load_spec()

    assets = data["production_assets"]

    assert assets["status"] == "production_validated"
    assert (
        assets["crt_preset"]
        == "retrovault/snes/classic/RetroVault_SNES_Classic_CRT.slangp"
    )

    validation = data["production_validation"]

    assert validation["status"] == "pass"
    assert validation["geometry"]["aspect_ratio"] == "4:3"
    assert validation["geometry"]["aspect_ratio_index"] == 23

    assert assets["png"].endswith(
        "RetroVault_SNES_Classic_1080p.png"
    )

    assert assets["descriptor"].endswith(
        "RetroVault_SNES_Classic.cfg"
    )

    assert assets["runtime_descriptor"].endswith(
        "RetroVault_SNES_Classic.runtime.cfg"
    )

    assert assets["shader_descriptor"].endswith(
        "RetroVault_SNES_Classic.shader.cfg"
    )

    assert assets["production_manifest"].endswith(
        "RetroVault_SNES_Classic.production.json"
    )


def test_native_snes_reference_is_portable():
    data = load_spec()

    assert data["catalog"]["planned_reference"] == (
        "retro-vault://overlays/"
        "retrovault/snes/classic/"
        "RetroVault_SNES_Classic.cfg"
    )

    assert data["catalog"]["reference"] == (
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
        selection["gameplay_aperture"]
        ["geometry_status"]
        == "production_alpha_locked"
    )

    assert (
        selection["right_panel"]
        ["controller_imagery"]
        == "excluded"
    )

    assert (
        selection["right_panel"]
        ["joystick_imagery"]
        == "excluded"
    )

    assert (
        selection["right_panel"]
        ["identity_element"]
        == "16-BIT"
    )

    assert (
        selection["lower_branding"]
        ["retrovault_position"]
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
        selection["lower_branding"]
        ["selection_status"]
        == "approved"
    )

    assert selection["controller"]["included"] is False


def test_native_snes_blended_aperture_contract():
    data = load_spec()

    aperture = (
        data["design"]
        ["master_visual_selection"]
        ["gameplay_aperture"]
    )

    assert (
        aperture["geometry_status"]
        == "production_alpha_locked"
    )

    assert aperture["legacy_geometry"] == {
        "x": 353,
        "y": 87,
        "width": 1216,
        "height": 750,
    }

    presentation = aperture["presentation"]

    assert "fully transparent" in presentation
    assert "soft CRT-style alpha blend" in presentation
    assert "all four sides" in presentation


def test_native_snes_safe_zone_is_production_locked():
    runtime = load_spec()["design"]["runtime"]

    safe_zone = runtime["safe_zone"]

    assert (
        safe_zone["status"]
        == "production_locked"
    )

    assert (
        "Branding"
        in safe_zone["policy"]
    )

    assert (
        "gameplay center"
        in safe_zone["policy"]
    )


def test_native_snes_blend_does_not_replace_game_aspect():
    runtime = load_spec()["design"]["runtime"]

    assert runtime["game_aspect"] == "4:3"

    policy = runtime["game_viewport"][
        "production_policy"
    ]

    assert "RetroArch" in policy
    assert "4:3" in policy


def test_native_snes_package_tracks_live_production_proof():
    data = load_spec()

    assert data["production_assets"]["status"] == "production_validated"

    validation = data["production_validation"]

    assert validation["status"] == "pass"
    assert validation["cross_game_validation"]["Super Mario World"] == "pass"
    assert (
        validation["cross_game_validation"]["Street Fighter II Turbo"]
        == "pass"
    )

    boundary = (
        data["design"]
        ["master_visual_selection"]
        ["production_boundary"]
    )

    assert "live RetroArch proof" in boundary
    assert "final production promotion" in boundary
