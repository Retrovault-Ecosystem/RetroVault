import json
from pathlib import Path

from services.presentation.platform_policy import (
    PlatformPresentationPolicyRegistry,
    PlatformPresentationPolicyState,
)

from services.presentation.master_profile import (
    MasterPresentationClass,
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



def test_genesis_geometry_matches_ready_production_package():
    data = _load_specification()
    geometry = data["geometry"]
    qualification = geometry["qualification"]
    state = data["production_state"]

    assert geometry["status"] == "runtime_geometry_qualified"

    assert geometry["canvas"] == {
        "width": 1920,
        "height": 1080,
    }

    assert geometry["aperture"] == {
        "x": 312,
        "y": 80,
        "width": 1296,
        "height": 770,
    }

    # A.3-N.5-B now records the real-content qualification result.
    # This is evidence for the universal CONTAIN implementation.
    # Production runtime must still derive geometry from each loaded
    # content/core display aspect rather than treating these values
    # as a game-specific fixed override.
    assert geometry["viewport"] == {
        "x": 373,
        "y": 80,
        "width": 1173,
        "height": 770,
    }
    assert geometry["aspect_ratio_index"] == 23
    assert geometry["integer_scaling"] is False
    assert geometry["viewport_bias_x"] == 0.5
    assert geometry["viewport_bias_y"] == 0.5
    assert geometry["crop_overscan"] is False

    assert geometry["runtime_geometry_policy"] == (
        "derive_per_loaded_content_display_aspect"
    )

    assert qualification["source"] == (
        "loaded_content_core_probe"
    )
    assert qualification["core_identity"] == (
        "genesis_plus_gx"
    )
    assert qualification["display_aspect_width"] == 1.524
    assert qualification["display_aspect_height"] == 1.0
    assert qualification["display_aspect"] == 1.524
    assert qualification["profile_class"] == "classic_4_3"
    assert qualification["fit_policy"] == "contain"

    assert qualification[
        "qualified_reference_viewport"
    ] == {
        "x": 373,
        "y": 80,
        "width": 1173,
        "height": 770,
    }

    assert qualification[
        "qualified_reference_margins"
    ] == {
        "left": 61,
        "right": 62,
        "top": 0,
        "bottom": 0,
    }

    assert qualification["runtime_geometry_policy"] == (
        "derive_per_loaded_content_display_aspect"
    )
    assert qualification["title_specific_geometry"] is False

    assert state["presentation_policy_state"] == "ready"
    assert state["production_package_complete"] is True
    assert state["production_ready"] is True
    assert state["live_calibration_complete"] is True



def test_genesis_is_ready_after_n5c_policy_activation():
    registry = PlatformPresentationPolicyRegistry

    assert (
        registry.state_for(
            "platform.sega.genesis"
        )
        == PlatformPresentationPolicyState.READY
    )

    assert (
        "platform.sega.genesis"
        in set(
            registry.ready_platform_ids()
        )
    )

    state = _specification()[
        "production_state"
    ]

    assert (
        state["presentation_policy_state"]
        == "ready"
    )

    assert (
        state["production_package_complete"]
        is True
    )

    assert (
        state["production_ready"]
        is True
    )

    assert (
        state["live_calibration_complete"]
        is True
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


def test_genesis_qualified_geometry_is_activated_by_n5c_policy():
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
        is True
    )
    assert (
        qualification["physical_runtime_geometry_qualified"]
        is True
    )

    assert (
        PlatformPresentationPolicyRegistry.state_for(
            platform_id
        )
        is PlatformPresentationPolicyState.READY
    )

    policy = (
        PlatformPresentationPolicyRegistry.for_platform(
            platform_id
        )
    )

    assert policy is not None
    assert policy.platform_id == platform_id
    assert policy.core_identities == ("genesis_plus_gx",)

    core_policy = (
        PlatformPresentationPolicyRegistry.for_core(
            "genesis_plus_gx"
        )
    )

    assert core_policy is not None
    assert core_policy.platform_id == platform_id
    assert core_policy.core_identities == ("genesis_plus_gx",)

    assert (
        PlatformPresentationPolicyRegistry
        .master_presentation_class_for(
            platform_id
        )
        is MasterPresentationClass.CLASSIC_4_3
    )

    assert platform_id in (
        PlatformPresentationPolicyRegistry
        .ready_platform_ids()
    )



def test_genesis_runtime_geometry_qualification_supports_ready_policy():
    data = _load_specification()

    qualification = data[
        "master_presentation_qualification"
    ]
    geometry = data["geometry"]
    state = data["production_state"]

    assert (
        qualification["physical_runtime_geometry_qualified"]
        is True
    )
    assert (
        qualification["production_policy_activation"]
        is True
    )

    assert geometry["status"] == "runtime_geometry_qualified"
    assert geometry["canvas"] == {
        "width": 1920,
        "height": 1080,
    }
    assert geometry["aperture"] == {
        "x": 312,
        "y": 80,
        "width": 1296,
        "height": 770,
    }
    assert geometry["viewport"] == {
        "x": 373,
        "y": 80,
        "width": 1173,
        "height": 770,
    }
    assert geometry["aspect_ratio_index"] == 23
    assert geometry["integer_scaling"] is False
    assert geometry["viewport_bias_x"] == 0.5
    assert geometry["viewport_bias_y"] == 0.5
    assert geometry["crop_overscan"] is False
    assert geometry["runtime_geometry_policy"] == (
        "derive_per_loaded_content_display_aspect"
    )

    evidence = geometry["qualification"]

    assert evidence["source"] == "loaded_content_core_probe"
    assert evidence["core_identity"] == "genesis_plus_gx"
    assert evidence["display_aspect_width"] == 1.524
    assert evidence["display_aspect_height"] == 1.0
    assert evidence["display_aspect"] == 1.524
    assert evidence["profile_class"] == "classic_4_3"
    assert evidence["fit_policy"] == "contain"
    assert evidence["qualified_reference_viewport"] == {
        "x": 373,
        "y": 80,
        "width": 1173,
        "height": 770,
    }
    assert evidence["qualified_reference_margins"] == {
        "left": 61,
        "right": 62,
        "top": 0,
        "bottom": 0,
    }
    assert evidence["title_specific_geometry"] is False

    assert state["presentation_policy_state"] == "ready"
    assert state["production_package_complete"] is True
    assert state["production_ready"] is True
    assert state["live_calibration_complete"] is True



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
