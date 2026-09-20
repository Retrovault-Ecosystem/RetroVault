import ast
from pathlib import Path


def test_app_starts_main_window_maximized():
    tree = ast.parse(
        Path("app.py").read_text(
            encoding="utf-8"
        )
    )

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    ]

    assert any(
        isinstance(call.func, ast.Attribute)
        and isinstance(
            call.func.value,
            ast.Name,
        )
        and call.func.value.id == "window"
        and call.func.attr == "showMaximized"
        for call in calls
    )


def test_app_does_not_start_main_window_with_plain_show():
    tree = ast.parse(
        Path("app.py").read_text(
            encoding="utf-8"
        )
    )

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    ]

    assert not any(
        isinstance(call.func, ast.Attribute)
        and isinstance(
            call.func.value,
            ast.Name,
        )
        and call.func.value.id == "window"
        and call.func.attr == "show"
        for call in calls
    )


def test_main_window_has_no_artificial_1200x800_resize():
    text = Path(
        "ui/main_window.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "self.resize(" not in text
