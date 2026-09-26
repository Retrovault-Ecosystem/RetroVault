from pathlib import Path


def test_game_details_preserves_effective_overlay_for_launch_profile():
    source = Path(
        "ui/library/details/game_details.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "overlay = presentation.overlay" in source
    assert "overlay=overlay," in source
    assert 'overlay="",' not in source


def test_game_details_has_no_content_specific_presentation_fix():
    source = Path(
        "ui/library/details/game_details.py"
    ).read_text(
        encoding="utf-8"
    ).casefold()

    forbidden = (
        "duck tales",
        "ducktales",
        "duck_tales",
        "duck-tales",
        "street fighter",
        "sonic the hedgehog",
    )

    for token in forbidden:
        assert token not in source
