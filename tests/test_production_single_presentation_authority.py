import json
from pathlib import Path

from services.presentation.models import (
    PresentationProfile,
)
from services.presentation.resolver import (
    PresentationResolver,
)


ROOT = Path(__file__).resolve().parents[1]

RECOMMENDATIONS = (
    ROOT
    / "data/presentation/recommendations.json"
)


def _recommendations():
    return json.loads(
        RECOMMENDATIONS.read_text(
            encoding="utf-8"
        )
    )


def test_nes_uses_native_overlay_and_screen_only_crt():
    data = _recommendations()

    profile = data["systems"][
        "platform.nintendo.nes"
    ]

    assert profile["overlay"].endswith(
        "/retrovault/nes/classic/"
        "RetroVault_NES_Classic.cfg"
    )

    assert profile["shader"].endswith(
        "/retrovault/nes/classic/"
        "RetroVault_NES_Classic_CRT.slangp"
    )

    assert "Orionsangel" not in profile["shader"]
    assert (
        "Nintendo_NES-[STD]"
        not in profile["shader"]
    )


def test_snes_uses_native_overlay_and_screen_only_crt():
    data = _recommendations()

    profile = data["systems"][
        "platform.nintendo.snes"
    ]

    assert profile["overlay"].endswith(
        "/retrovault/snes/classic/"
        "RetroVault_SNES_Classic.cfg"
    )

    assert profile["shader"].endswith(
        "/retrovault/snes/classic/"
        "RetroVault_SNES_Classic_CRT.slangp"
    )

    assert "Orionsangel" not in profile["shader"]
    assert (
        "Nintendo_SNES-[STD]"
        not in profile["shader"]
    )


def test_super_metroid_has_no_game_level_presentation_authority():
    data = _recommendations()

    profile = data["games"][
        "game.super_metroid"
    ]

    assert profile == {
        "shader": "",
        "overlay": "",
        "artwork": "",
    }


def test_empty_game_profile_inherits_system_authority():
    system = PresentationProfile(
        shader="system-crt",
        overlay="system-overlay",
        artwork="",
    )

    game = PresentationProfile(
        shader="",
        overlay="",
        artwork="",
    )

    effective = PresentationResolver._merge(
        system,
        game,
    )

    assert effective.shader == "system-crt"
    assert effective.overlay == "system-overlay"


def test_native_crt_presets_reference_screen_only_base():
    expected = (
        "MBZ__0__SMOOTH-ADV-"
        "SCREEN-ONLY__GDV.slangp"
    )

    paths = (
        ROOT
        / "data/presentation/shaders/"
          "retrovault/nes/classic/"
          "RetroVault_NES_Classic_CRT.slangp",

        ROOT
        / "data/presentation/shaders/"
          "retrovault/snes/classic/"
          "RetroVault_SNES_Classic_CRT.slangp",
    )

    for path in paths:
        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        assert expected in text
