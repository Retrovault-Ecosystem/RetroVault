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
    assert "console photography" in originality
    assert "external pack artwork" in originality
    assert "third-party trademark" in originality
    assert "ownership of those marks is not claimed" in originality


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



def test_native_nes_specification_is_production_asset():
    data = load_spec()

    assert data["production_status"] == "production"

def test_native_nes_canvas_geometry():
    runtime = load_spec()["design"]["runtime"]

    assert runtime["canvas"] == {
        "width": 1920,
        "height": 1080,
    }



def test_native_nes_game_viewport_geometry():
    viewport = (
        load_spec()["design"]["runtime"][
            "game_viewport"
        ]
    )

    assert viewport["x"] == 355
    assert viewport["y"] == 100
    assert viewport["width"] == 1188
    assert viewport["height"] == 751

def test_native_nes_game_viewport_is_inside_canvas():
    runtime = load_spec()["design"]["runtime"]

    canvas = runtime["canvas"]
    viewport = runtime["game_viewport"]

    assert viewport["x"] >= 0
    assert viewport["y"] >= 0

    assert (
        viewport["x"] + viewport["width"]
        <= canvas["width"]
    )

    assert (
        viewport["y"] + viewport["height"]
        <= canvas["height"]
    )



def test_native_nes_game_viewport_normalization():
    viewport = (
        load_spec()["design"]["runtime"][
            "game_viewport"
        ]
    )

    normalized = viewport["normalized"]

    assert normalized["x"] == 355 / 1920
    assert normalized["y"] == 100 / 1080
    assert normalized["width"] == 1188 / 1920
    assert normalized["height"] == 751 / 1080

def test_native_nes_branding_layout_is_approved():
    layout = load_spec()["design"][
        "branding_layout"
    ]

    assert (
        layout["system_identity"]["position"]
        == "bottom-center-below-retrovault"
    )

    assert (
        layout["retrovault_identity"]["position"]
        == "bottom-center"
    )


def test_native_nes_viewport_requires_transparency():
    policy = (
        load_spec()["design"]["runtime"][
            "game_viewport"
        ]["policy"]
    )

    assert "fully transparent" in policy



def test_native_nes_aperture_is_not_game_aspect_contract():
    data = load_spec()

    runtime = data["design"]["runtime"]
    composition = data["design"]["composition"]

    assert runtime["game_aspect"] == "4:3"

    assert (
        runtime["game_viewport"]["aperture_aspect"]
        == "1188:751"
    )

    assert (
        "RetroArch"
        in runtime["game_viewport"]["policy"]
    )

    assert (
        "shader"
        in runtime["game_viewport"]["policy"]
    )

    assert (
        "gameplay"
        in composition["game_view"].lower()
    )


def test_native_nes_aperture_ratio_matches_geometry():
    viewport = (
        load_spec()["design"]["runtime"][
            "game_viewport"
        ]
    )

    width = viewport["width"]
    height = viewport["height"]

    assert width == 1188
    assert height == 751

    assert (
        viewport["aperture_aspect"]
        == f"{width}:{height}"
    )

    assert (
        width / height
        == 1188 / 751
    )

def test_native_nes_final_branding_layout():
    layout = load_spec()["design"]["branding_layout"]

    assert (
        layout["retrovault_identity"]["position"]
        == "bottom-center"
    )

    assert (
        layout["system_identity"]["position"]
        == "bottom-center-below-retrovault"
    )

    assert "red accent lines" in (
        layout["retrovault_identity"]["accent"]
    )

    assert "without flanking red lines" in (
        layout["system_identity"]["accent"]
    )


def test_native_nes_premium_finish_contract():
    finish = load_spec()["design"]["finish"]

    assert finish["quality_target"] == "premium showroom"

    assert "naturally used" in finish["controls"]
    assert "subtle wear" in finish["controls"]

    assert "exceptionally crisp" in finish["branding"]
    assert "precisely aligned" in finish["branding"]
    assert "evenly spaced" in finish["branding"]


def test_native_nes_master_visual_language_contract():
    finish = load_spec()["design"]["finish"]

    assert "master direction" in finish["consistency"]
    assert "bezel and overlay families" in (
        finish["consistency"]
    )


def test_native_nes_branding_remains_outside_aperture():
    policy = (
        load_spec()["design"]["runtime"][
            "safe_zone"
        ]["policy"]
    )

    assert "outside the transparent gameplay" in policy
    assert "lower presentation area" in policy


def test_native_nes_provenance_does_not_claim_platform_marks():
    data = load_spec()

    assert (
        "Original RetroVault bezel composition"
        in data["copyright"]
    )

    assert (
        "Third-party trademarks"
        in data["copyright"]
    )

    assert (
        "ownership of those marks is not claimed"
        in data["design"]["originality"]
    )


def test_native_nes_platform_identity_is_secondary():
    data = load_spec()

    branding = data["design"]["composition"]["branding"]
    policy = data["trademark_policy"]

    assert (
        "RetroVault is the primary presentation identity"
        in branding
    )

    assert (
        "Platform identification is secondary"
        in branding
    )

    assert (
        "not claimed as RetroVault intellectual property"
        in policy["platform_identity"]
    )


def test_native_nes_catalog_attribution_is_precise():
    attribution = load_spec()["catalog"]["attribution"]

    assert (
        "Original RetroVault bezel composition"
        in attribution
    )

    assert (
        "trademarks are the property"
        in attribution
    )


def test_native_nes_provenance_preserves_original_asset_boundary():
    originality = load_spec()["design"]["originality"]

    assert "frame treatment" in originality
    assert "presentation design" in originality
    assert "console photography" in originality
    assert "external pack artwork" in originality
