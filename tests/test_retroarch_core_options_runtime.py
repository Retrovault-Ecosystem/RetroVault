from pathlib import Path

import pytest

from services.retroarch.core_options_runtime import (
    CoreOptionsRuntimeConfig,
)


def test_fceumm_policy_preserves_all_four_edges():
    policy = CoreOptionsRuntimeConfig.policy_for(
        "/cores/fceumm_libretro.so"
    )

    assert policy == {
        "fceumm_overscan_h_left": "0",
        "fceumm_overscan_h_right": "0",
        "fceumm_overscan_v_top": "0",
        "fceumm_overscan_v_bottom": "0",
    }


@pytest.mark.parametrize(
    "core",
    (
        "/cores/fceumm_libretro.so",
        "/cores/lr-fceumm_libretro.so",
        "fceumm_libretro.so",
        "fceumm",
    ),
)
def test_fceumm_identity_variants_share_policy(
    core,
):
    assert (
        CoreOptionsRuntimeConfig.policy_for(
            core
        )
        == CoreOptionsRuntimeConfig.POLICIES[
            "fceumm"
        ]
    )


def test_unmanaged_core_has_no_runtime_policy():
    assert (
        CoreOptionsRuntimeConfig.policy_for(
            "/cores/example_libretro.so"
        )
        == {}
    )


def test_create_writes_transient_fceumm_options(
    tmp_path,
):
    runtime = CoreOptionsRuntimeConfig(
        directory=tmp_path
    )

    result = runtime.create(
        "/cores/fceumm_libretro.so"
    )

    path = Path(
        result
    )

    assert path.is_file()

    assert path.read_text(
        encoding="utf-8"
    ) == (
        'fceumm_overscan_h_left = "0"\n'
        'fceumm_overscan_h_right = "0"\n'
        'fceumm_overscan_v_top = "0"\n'
        'fceumm_overscan_v_bottom = "0"\n'
    )

    runtime.cleanup()

    assert not path.exists()


def test_create_returns_none_for_unmanaged_core(
    tmp_path,
):
    runtime = CoreOptionsRuntimeConfig(
        directory=tmp_path
    )

    assert (
        runtime.create(
            "/cores/example_libretro.so"
        )
        is None
    )

    assert list(
        tmp_path.glob("*")
    ) == []


def test_invalid_core_type_is_rejected():
    with pytest.raises(
        ValueError,
        match="Core path must be a string",
    ):
        CoreOptionsRuntimeConfig.policy_for(
            None
        )


def test_empty_core_is_rejected():
    with pytest.raises(
        ValueError,
        match="Core path cannot be empty",
    ):
        CoreOptionsRuntimeConfig.policy_for(
            ""
        )


def test_create_forwards_platform_identity_to_policy_resolution(
    tmp_path,
    monkeypatch,
):
    from services.retroarch.core_options_runtime import (
        CoreOptionsRuntimeConfig,
    )

    runtime = CoreOptionsRuntimeConfig(
        directory=tmp_path,
    )

    observed = {}
    original = runtime.policy_for

    def observing_policy_for(
        core,
        platform_id=None,
    ):
        observed["core"] = core
        observed["platform_id"] = platform_id

        return original(
            core,
            platform_id=platform_id,
        )

    monkeypatch.setattr(
        runtime,
        "policy_for",
        observing_policy_for,
    )

    path = runtime.create(
        "/cores/fceumm_libretro.so",
        platform_id="platform.nintendo.nes",
    )

    assert observed == {
        "core": "/cores/fceumm_libretro.so",
        "platform_id": "platform.nintendo.nes",
    }

    assert path is not None


def test_create_rejects_platform_core_mismatch_before_file_creation(
    tmp_path,
):
    from services.retroarch.core_options_runtime import (
        CoreOptionsRuntimeConfig,
    )

    runtime = CoreOptionsRuntimeConfig(
        directory=tmp_path,
    )

    try:
        runtime.create(
            "/cores/snes9x_libretro.so",
            platform_id="platform.nintendo.nes",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected platform/core mismatch."
        )

    assert list(
        tmp_path.iterdir()
    ) == []
