import pytest

from services.presentation import (
    PresentationAssetReferenceResolver,
    PresentationProfile,
)


def make_roots(tmp_path):
    shader_root = tmp_path / "shaders"
    overlay_root = tmp_path / "overlays"
    artwork_root = tmp_path / "artwork"

    shader_root.mkdir()
    overlay_root.mkdir()
    artwork_root.mkdir()

    return shader_root, overlay_root, artwork_root


def make_resolver(tmp_path):
    shader_root, overlay_root, artwork_root = make_roots(
        tmp_path
    )

    resolver = PresentationAssetReferenceResolver(
        shader_root=shader_root,
        overlay_root=overlay_root,
        artwork_root=artwork_root,
    )

    return (
        resolver,
        shader_root,
        overlay_root,
        artwork_root,
    )


def test_portable_shader_reference_resolves_under_shader_root(
    tmp_path,
):
    resolver, shader_root, _, _ = make_resolver(tmp_path)

    preset = (
        shader_root
        / "platform.nintendo.nes"
        / "default.slangp"
    )
    preset.parent.mkdir(parents=True)
    preset.write_text("shader", encoding="utf-8")

    assert resolver.resolve_reference(
        "retro-vault://shaders/"
        "platform.nintendo.nes/default.slangp"
    ) == str(preset.resolve())


def test_asset_namespaces_remain_independent(tmp_path):
    resolver, shader_root, overlay_root, artwork_root = (
        make_resolver(tmp_path)
    )

    shader = shader_root / "nes" / "default.slangp"
    overlay = overlay_root / "nes" / "default.cfg"
    artwork = artwork_root / "nes" / "default.png"

    for path in (shader, overlay, artwork):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("asset", encoding="utf-8")

    profile = resolver.resolve_profile(
        PresentationProfile(
            shader="retro-vault://shaders/nes/default.slangp",
            overlay="retro-vault://overlays/nes/default.cfg",
            artwork="retro-vault://artwork/nes/default.png",
        )
    )

    assert profile == PresentationProfile(
        shader=str(shader.resolve()),
        overlay=str(overlay.resolve()),
        artwork=str(artwork.resolve()),
    )


def test_empty_profile_remains_empty(tmp_path):
    resolver, _, _, _ = make_resolver(tmp_path)

    assert resolver.resolve_profile(
        PresentationProfile()
    ) == PresentationProfile()


def test_existing_local_values_are_preserved(tmp_path):
    resolver, _, _, _ = make_resolver(tmp_path)

    profile = PresentationProfile(
        shader="/existing/manual.slangp",
        overlay="/existing/manual.cfg",
        artwork="/existing/manual.png",
    )

    assert resolver.resolve_profile(profile) == profile


def test_missing_portable_asset_is_rejected(tmp_path):
    resolver, _, _, _ = make_resolver(tmp_path)

    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        resolver.resolve_reference(
            "retro-vault://shaders/nes/missing.slangp"
        )


def test_unconfigured_asset_root_is_rejected(tmp_path):
    resolver = PresentationAssetReferenceResolver(
        shader_root=tmp_path / "shaders"
    )

    with pytest.raises(
        ValueError,
        match="No local presentation asset root",
    ):
        resolver.resolve_reference(
            "retro-vault://overlays/nes/default.cfg"
        )


def test_unknown_asset_namespace_is_rejected(tmp_path):
    resolver, _, _, _ = make_resolver(tmp_path)

    with pytest.raises(
        ValueError,
        match="Unsupported",
    ):
        resolver.resolve_reference(
            "retro-vault://unknown/nes/default.asset"
        )


@pytest.mark.parametrize(
    "reference",
    [
        "retro-vault://shaders",
        "retro-vault://shaders/",
        "retro-vault://shaders/../outside.slangp",
        "retro-vault://shaders/nes/default.slangp?variant=x",
        "retro-vault://shaders/nes/default.slangp#fragment",
    ],
)
def test_malformed_or_unsafe_reference_is_rejected(
    tmp_path,
    reference,
):
    resolver, _, _, _ = make_resolver(tmp_path)

    with pytest.raises(ValueError):
        resolver.resolve_reference(reference)


@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        {},
    ],
)
def test_reference_requires_string(tmp_path, value):
    resolver, _, _, _ = make_resolver(tmp_path)

    with pytest.raises(
        TypeError,
        match="must be a string",
    ):
        resolver.resolve_reference(value)


def test_profile_requires_presentation_profile(tmp_path):
    resolver, _, _, _ = make_resolver(tmp_path)

    with pytest.raises(
        TypeError,
        match="PresentationProfile",
    ):
        resolver.resolve_profile({})


def test_symlink_cannot_escape_configured_asset_root(
    tmp_path,
):
    resolver, shader_root, _, _ = make_resolver(tmp_path)

    outside = tmp_path / "outside"
    outside.mkdir()

    escaped = outside / "escaped.slangp"
    escaped.write_text(
        "outside",
        encoding="utf-8",
    )

    link = shader_root / "linked"
    link.symlink_to(
        outside,
        target_is_directory=True,
    )

    with pytest.raises(
        ValueError,
        match="escapes",
    ):
        resolver.resolve_reference(
            "retro-vault://shaders/"
            "linked/escaped.slangp"
        )
