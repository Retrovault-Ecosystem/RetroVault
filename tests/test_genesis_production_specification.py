import json
from pathlib import Path

from services.presentation.platform_policy import (
    PlatformPresentationPolicyRegistry,
    PlatformPresentationPolicyState,
)


ROOT = Path(__file__).resolve().parents[1]

SPECIFICATION = (
    ROOT
    / "data"
    / "presentation"
    / "specifications"
    / "rvv_genesis_classic.json"
)


def _specification():
    return json.loads(
        SPECIFICATION.read_text(
            encoding="utf-8",
        )
    )


def test_genesis_specification_uses_canonical_platform_identity():
    specification = _specification()

    assert (
        specification["platform_id"]
        == "platform.sega.genesis"
    )

    assert (
        specification["production_core"]["identity"]
        == "genesis_plus_gx"
    )

    assert (
        specification["production_core"]["rvdb_core_id"]
        == "core.genesis.plus.gx"
    )


def test_genesis_specification_matches_canonical_core_authority():
    registry = PlatformPresentationPolicyRegistry

    assert (
        registry.compatible_core_identities(
            "platform.sega.genesis"
        )
        == ("genesis_plus_gx",)
    )


def test_genesis_specification_preserves_all_source_edges():
    source = _specification()[
        "source_preservation"
    ]

    assert source["contract"] == (
        "preserve_legitimate_source_content"
    )

    assert set(source["edges"]) == {
        "top",
        "right",
        "bottom",
        "left",
    }

    assert (
        source["crop_policy"]
        == "no_unvalidated_crop"
    )

    assert (
        source["title_specific_geometry"]
        is False
    )


def test_genesis_specification_has_single_presentation_authority():
    authority = _specification()[
        "presentation_authority"
    ]

    assert authority[
        "overlay_authority_count"
    ] == 1

    assert authority[
        "shader_authority_count"
    ] == 1

    assert authority[
        "session_isolation_required"
    ] is True

    assert authority[
        "clear_inherited_overlay"
    ] is True

    assert authority[
        "clear_inherited_shader"
    ] is True

    assert authority[
        "physical_geometry_owner"
    ] == "platform_package"

    assert authority[
        "shader_may_own_physical_geometry"
    ] is False


def test_genesis_geometry_is_deliberately_unqualified():
    geometry = _specification()["geometry"]

    assert geometry["status"] == "unqualified"

    for key in (
        "canvas",
        "aperture",
        "viewport",
        "aspect_ratio_index",
        "integer_scaling",
        "viewport_bias_x",
        "viewport_bias_y",
        "crop_overscan",
    ):
        assert geometry[key] is None


def test_genesis_cannot_be_ready_during_n5a():
    registry = PlatformPresentationPolicyRegistry

    assert (
        registry.state_for(
            "platform.sega.genesis"
        )
        == PlatformPresentationPolicyState.UNCONFIGURED
    )

    assert (
        "platform.sega.genesis"
        not in set(
            registry.ready_platform_ids()
        )
    )

    state = _specification()[
        "production_state"
    ]

    assert (
        state["presentation_policy_state"]
        == "unconfigured"
    )

    assert (
        state["production_package_complete"]
        is False
    )

    assert (
        state["production_ready"]
        is False
    )

    assert (
        state["live_calibration_complete"]
        is False
    )


def test_genesis_specification_contains_no_title_or_rom_identity():
    specification = _specification()

    serialized = json.dumps(
        specification,
        sort_keys=True,
    ).lower()

    forbidden = (
        '"game_id"',
        '"game_name"',
        '"rom"',
        '"rom_path"',
        '"title_id"',
        '"title_name"',
    )

    for token in forbidden:
        assert token not in serialized



def _load_specification():
    import json
    from pathlib import Path

    return json.loads(
        Path(
            "data/presentation/specifications/"
            "rvv_genesis_classic.json"
        ).read_text(encoding="utf-8")
    )


def test_genesis_has_preproduction_master_presentation_qualification():
    from services.presentation.master_profile import (
        MasterPresentationClass,
        MasterPresentationProfileRegistry,
        MasterPresentationQualification,
        PresentationFitPolicy,
        master_presentation_qualification,
    )

    data = _load_specification()

    qualification = data[
        "master_presentation_qualification"
    ]

    assert qualification["status"] == (
        "preproduction_qualified"
    )
    assert qualification["master_presentation_class"] == (
        "classic_4_3"
    )
    assert qualification["resolved_display_aspect"] == {
        "width": 4,
        "height": 3,
    }
    assert qualification["fit_policy"] == "contain"

    profile_class = MasterPresentationClass(
        qualification["master_presentation_class"]
    )

    assert (
        master_presentation_qualification(profile_class)
        is MasterPresentationQualification.QUALIFIED
    )

    profile = MasterPresentationProfileRegistry.require(
        profile_class
    )

    assert (
        profile.fit_policy
        is PresentationFitPolicy.CONTAIN
    )

    geometry = profile.contain_aspect(
        qualification["resolved_display_aspect"]["width"],
        qualification["resolved_display_aspect"]["height"],
    )

    assert qualification["master_canvas"] == {
        "width": profile.canvas_width,
        "height": profile.canvas_height,
    }

    assert qualification["master_safe_envelope"] == {
        "x": geometry.x,
        "y": geometry.y,
        "width": geometry.width,
        "height": geometry.height,
    }

    assert (
        geometry.x,
        geometry.y,
        geometry.width,
        geometry.height,
    ) == (
        240,
        0,
        1440,
        1080,
    )


def test_genesis_preproduction_qualification_does_not_activate_policy():
    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
        PlatformPresentationPolicyState,
    )

    data = _load_specification()
    platform_id = data["platform_id"]

    qualification = data[
        "master_presentation_qualification"
    ]

    assert (
        qualification["production_policy_activation"]
        is False
    )
    assert (
        qualification["physical_runtime_geometry_qualified"]
        is False
    )

    assert (
        PlatformPresentationPolicyRegistry.state_for(
            platform_id
        )
        is PlatformPresentationPolicyState.UNCONFIGURED
    )

    assert (
        PlatformPresentationPolicyRegistry.for_platform(
            platform_id
        )
        is None
    )

    assert (
        PlatformPresentationPolicyRegistry.for_core(
            "genesis_plus_gx"
        )
        is None
    )

    assert (
        PlatformPresentationPolicyRegistry
        .master_presentation_class_for(platform_id)
        is None
    )

    assert platform_id not in (
        PlatformPresentationPolicyRegistry
        .ready_platform_ids()
    )


def test_genesis_preproduction_qualification_keeps_physical_geometry_unqualified():
    data = _load_specification()

    qualification = data[
        "master_presentation_qualification"
    ]
    geometry = data["geometry"]
    state = data["production_state"]

    assert (
        qualification["physical_runtime_geometry_qualified"]
        is False
    )

    assert geometry["status"] == "unqualified"

    for key in (
        "canvas",
        "aperture",
        "viewport",
        "aspect_ratio_index",
        "integer_scaling",
        "viewport_bias_x",
        "viewport_bias_y",
        "crop_overscan",
    ):
        assert geometry[key] is None

    assert (
        state["presentation_policy_state"]
        == "unconfigured"
    )
    assert state["production_package_complete"] is False
    assert state["production_ready"] is False
    assert state["live_calibration_complete"] is False


def test_genesis_master_qualification_contains_no_game_identity():
    import json

    data = _load_specification()

    payload = json.dumps(
        data["master_presentation_qualification"],
        sort_keys=True,
    ).casefold()

    forbidden = (
        "game_id",
        "rom_filename",
        "archive_filename",
        "title_specific_geometry",
    )

    for identity in forbidden:
        assert identity not in payload
