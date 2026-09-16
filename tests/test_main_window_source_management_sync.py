from pathlib import Path


def _main_window_text():
    return Path(
        "ui/main_window.py"
    ).read_text(
        encoding="utf-8"
    )


def _settings_text():
    return Path(
        "ui/pages/settings_page.py"
    ).read_text(
        encoding="utf-8"
    )


def test_settings_exposes_library_sources_changed_signal():
    text = _settings_text()

    assert (
        "library_sources_changed = pyqtSignal()"
        in text
    )


def test_successful_source_management_emits_live_change_signal():
    text = _settings_text()

    for status in (
        "Library source renamed",
        "Library source enabled",
        "Library source removed",
    ):
        position = text.index(
            status
        )

        following = text[
            position:
            position + 500
        ]

        assert (
            "library_sources_changed.emit()"
            in following
        )


def test_source_management_errors_do_not_emit_before_success():
    text = _settings_text()

    rename_start = text.index(
        "    def _rename_library_source("
    )
    toggle_start = text.index(
        "    def _toggle_library_source("
    )
    remove_start = text.index(
        "    def _remove_library_source("
    )

    rename = text[
        rename_start:toggle_start
    ]
    toggle = text[
        toggle_start:remove_start
    ]

    populate_start = text.index(
        "    def _populate(",
        remove_start,
    )

    remove = text[
        remove_start:populate_start
    ]

    for method in (
        rename,
        toggle,
        remove,
    ):
        assert (
            method.count(
                "library_sources_changed.emit()"
            )
            == 1
        )

        emit = method.index(
            "library_sources_changed.emit()"
        )

        success_status = method.rfind(
            "self.save_status.setText(",
            0,
            emit,
        )

        assert success_status != -1


def test_main_window_reloads_library_after_source_change():
    text = _main_window_text()

    assert (
        "def library_sources_changed() -> None:"
        in text
    )

    assert (
        "games = controller.reload_sources()"
        in text
    )

    assert (
        "settings_page.library_sources_changed.connect("
        in text
    )


def test_source_reload_refreshes_all_library_surfaces():
    text = _main_window_text()

    start = text.index(
        "        def library_sources_changed() -> None:"
    )

    end = text.index(
        "        settings_page.library_sources_changed.connect(",
        start,
    )

    callback = text[
        start:end
    ]

    required = (
        "controller.reload_sources()",
        "library_page.set_games(",
        "systems_page.refresh_page()",
        "playlists_page.refresh_collections(",
    )

    for token in required:
        assert token in callback


def test_source_reload_happens_before_surface_refresh():
    text = _main_window_text()

    start = text.index(
        "        def library_sources_changed() -> None:"
    )

    end = text.index(
        "        settings_page.library_sources_changed.connect(",
        start,
    )

    callback = text[
        start:end
    ]

    reload_position = callback.index(
        "controller.reload_sources()"
    )

    assert reload_position < callback.index(
        "library_page.set_games("
    )
    assert reload_position < callback.index(
        "systems_page.refresh_page()"
    )
    assert reload_position < callback.index(
        "playlists_page.refresh_collections("
    )


def test_source_reload_failure_is_reported_inline_without_popup():
    text = _main_window_text()

    start = text.index(
        "        def library_sources_changed() -> None:"
    )

    end = text.index(
        "        settings_page.library_sources_changed.connect(",
        start,
    )

    callback = text[
        start:end
    ]

    assert "try:" in callback
    assert "controller.reload_sources()" in callback

    assert (
        "except (\n"
        "                OSError,\n"
        "                RuntimeError,\n"
        "                ValueError,\n"
        "            ) as exc:"
        in callback
    )

    assert (
        "settings_page.save_status.setText("
        in callback
    )

    assert (
        '"Library source saved, but live "'
        in callback
    )

    assert (
        'f"reload failed: {exc}"'
        in callback
    )

    assert "QMessageBox" not in callback
    assert ".warning(" not in callback
    assert ".critical(" not in callback


def test_source_reload_failure_returns_before_surface_mutation():
    text = _main_window_text()

    start = text.index(
        "        def library_sources_changed() -> None:"
    )

    end = text.index(
        "        settings_page.library_sources_changed.connect(",
        start,
    )

    callback = text[
        start:end
    ]

    failure_message = callback.index(
        "settings_page.save_status.setText("
    )

    return_position = callback.index(
        "return",
        failure_message,
    )

    library_refresh = callback.index(
        "library_page.set_games("
    )

    systems_refresh = callback.index(
        "systems_page.refresh_page()"
    )

    playlists_refresh = callback.index(
        "playlists_page.refresh_collections("
    )

    assert return_position < library_refresh
    assert return_position < systems_refresh
    assert return_position < playlists_refresh


def test_source_reload_success_still_refreshes_all_surfaces():
    text = _main_window_text()

    start = text.index(
        "        def library_sources_changed() -> None:"
    )

    end = text.index(
        "        settings_page.library_sources_changed.connect(",
        start,
    )

    callback = text[
        start:end
    ]

    reload_position = callback.index(
        "controller.reload_sources()"
    )

    library_position = callback.index(
        "library_page.set_games("
    )

    systems_position = callback.index(
        "systems_page.refresh_page()"
    )

    playlists_position = callback.index(
        "playlists_page.refresh_collections("
    )

    assert reload_position < library_position
    assert reload_position < systems_position
    assert reload_position < playlists_position
