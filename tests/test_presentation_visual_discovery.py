import pytest

from services.presentation.visual_catalog import (
    VisualAsset,
    VisualAssetSource,
    VisualAssetType,
)
from services.presentation.visual_discovery import (
    VisualAssetDiscovery,
)


def asset(
    identity,
    display_name,
    *,
    source=VisualAssetSource.RVV_NATIVE,
    asset_type=VisualAssetType.OVERLAY,
    author="RetroVault",
    attribution="RetroVault visual",
    reference=None,
):
    return VisualAsset(
        id=identity,
        display_name=display_name,
        asset_type=asset_type,
        source=source,
        reference=(
            reference
            or (
                "retro-vault://overlays/"
                + identity
                + ".cfg"
            )
        ),
        author=author,
        attribution=attribution,
    )


def sample_assets():
    return (
        asset(
            "rvv.overlay.snes.classic",
            "Nintendo SNES — RetroVault Classic",
        ),
        asset(
            "rvv.overlay.nes.classic",
            "Nintendo NES — RetroVault Classic",
        ),
        asset(
            "retroarch.overlay.arcade",
            "RetroArch Arcade Overlay",
            source=VisualAssetSource.RETROARCH,
            author="RetroArch",
            attribution="RetroArch default visual",
        ),
        asset(
            "third-party.overlay.nes",
            "NES Community Bezel",
            source=VisualAssetSource.THIRD_PARTY,
            author="Community",
            attribution="Third-party visual",
        ),
    )


def test_discovery_accepts_visual_assets():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    assert len(discovery.assets) == 4


def test_discovery_rejects_non_iterable():
    with pytest.raises(
        TypeError,
        match="iterable",
    ):
        VisualAssetDiscovery(None)


def test_discovery_rejects_string_iterable():
    with pytest.raises(
        TypeError,
        match="iterable",
    ):
        VisualAssetDiscovery("visual")


def test_discovery_rejects_non_visual_entry():
    with pytest.raises(
        TypeError,
        match="VisualAsset",
    ):
        VisualAssetDiscovery([object()])


def test_all_returns_display_name_sorted_assets():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    assert [
        item.display_name
        for item in discovery.all()
    ] == [
        "NES Community Bezel",
        "Nintendo NES — RetroVault Classic",
        "Nintendo SNES — RetroVault Classic",
        "RetroArch Arcade Overlay",
    ]


def test_search_is_case_insensitive():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    assert {
        item.id
        for item in discovery.search("nEs")
    } == {
        "rvv.overlay.nes.classic",
        "third-party.overlay.nes",
    }


def test_search_does_not_match_inside_token():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    assert (
        "rvv.overlay.snes.classic"
        not in {
            item.id
            for item in discovery.search("nes")
        }
    )


def test_search_supports_prefix_matching():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    assert {
        item.id
        for item in discovery.search("retro")
    } == {
        "retroarch.overlay.arcade",
        "rvv.overlay.nes.classic",
        "rvv.overlay.snes.classic",
    }


def test_portable_reference_is_not_free_text_metadata():
    discovery = VisualAssetDiscovery(
        (
            asset(
                "community.asset",
                "Community Bezel",
                source=VisualAssetSource.THIRD_PARTY,
                author="Community",
                attribution="Third-party visual",
                reference=(
                    "retro-vault://overlays/"
                    "community.asset.cfg"
                ),
            ),
        )
    )

    assert discovery.search("retro") == ()


def test_search_matches_multiple_terms():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    assert [
        item.id
        for item in discovery.search(
            "retroVault snes"
        )
    ] == [
        "rvv.overlay.snes.classic",
    ]


def test_search_normalizes_whitespace():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    assert [
        item.id
        for item in discovery.search(
            "  Nintendo   NES  "
        )
    ] == [
        "rvv.overlay.nes.classic",
    ]


def test_search_matches_author():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    assert [
        item.id
        for item in discovery.search(
            "community"
        )
    ] == [
        "third-party.overlay.nes",
    ]


def test_search_matches_source_identity():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    assert [
        item.id
        for item in discovery.search(
            "third_party"
        )
    ] == [
        "third-party.overlay.nes",
    ]


def test_for_source_filters_exact_enum():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    assert [
        item.id
        for item in discovery.for_source(
            VisualAssetSource.RVV_NATIVE
        )
    ] == [
        "rvv.overlay.nes.classic",
        "rvv.overlay.snes.classic",
    ]


def test_for_source_rejects_string_filter():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    with pytest.raises(
        TypeError,
        match="VisualAssetSource",
    ):
        discovery.for_source(
            "rvv_native"
        )


def test_for_type_filters_exact_enum():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    assert len(
        discovery.for_type(
            VisualAssetType.OVERLAY
        )
    ) == 4


def test_for_type_rejects_string_filter():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    with pytest.raises(
        TypeError,
        match="VisualAssetType",
    ):
        discovery.for_type(
            "overlay"
        )


def test_query_combines_text_source_and_type():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    assert [
        item.id
        for item in discovery.query(
            text="Nintendo",
            source=VisualAssetSource.RVV_NATIVE,
            asset_type=VisualAssetType.OVERLAY,
        )
    ] == [
        "rvv.overlay.nes.classic",
        "rvv.overlay.snes.classic",
    ]


def test_query_none_text_means_no_text_filter():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    assert discovery.query(
        text=None
    ) == discovery.all()


def test_query_rejects_non_string_text():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    with pytest.raises(
        TypeError,
        match="query",
    ):
        discovery.query(
            text=123
        )


def test_empty_result_is_tuple():
    discovery = VisualAssetDiscovery(
        sample_assets()
    )

    result = discovery.search(
        "does-not-exist"
    )

    assert result == ()
    assert isinstance(
        result,
        tuple,
    )
