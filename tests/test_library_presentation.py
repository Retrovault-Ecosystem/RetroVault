from PyQt6.QtWidgets import QApplication


# QWidget-based Library presentation tests require a live
# QApplication before any widget is constructed. Keep one
# module-scoped reference so Qt cannot destroy the application
# between tests.
_RETROVAULT_LIBRARY_PRESENTATION_TEST_APP = (
    QApplication.instance()
    or QApplication([])
)


from pathlib import Path

from PyQt6.QtWidgets import QApplication

from ui.library.widgets.game_card import GameCard
from ui.library.widgets.view_selector import ViewSelector
from ui.library.views.details_view import DetailsView
from ui.library.views.compact_view import CompactView
from ui.library.details.game_details import GameDetails
from ui.themes.library import library_stylesheet


class Game:
    name = "Presentation Test"
    platform = "NES"
    year = 1987
    core = "lr-fceumm"
    artwork = ""
    favorite = False
    rom = ""


_QT_APP = None


def _app():
    global _QT_APP

    if _QT_APP is None:
        _QT_APP = (
            QApplication.instance()
            or QApplication([])
        )

    return _QT_APP


def test_library_theme_contract():
    stylesheet = library_stylesheet()

    for token in (
        "LibraryPage",
        "LibraryToolbar",
        "LibraryTitle",
        "LibrarySubtitle",
        "LibraryViewStack",
        "LibraryGameCard",
        "LibraryGameDetails",
        "LibraryLaunchAction",
        "#55c7e8",
    ):
        assert token in stylesheet


def test_theme_composition_contract():
    source = Path("ui/theme.py").read_text()

    assert (
        "from ui.themes.library import "
        "library_stylesheet"
    ) in source

    assert "+ library_stylesheet()" in source


def test_game_card_semantics_replace_legacy_inline_qss():
    _app()
    card = GameCard(Game())

    assert card.objectName() == "LibraryGameCard"
    assert card.cover.objectName() == "LibraryGameCover"
    assert card.title.objectName() == "LibraryGameTitle"
    assert card.info.objectName() == "LibraryGameInfo"

    source = Path(
        "ui/library/widgets/game_card.py"
    ).read_text()

    assert "#e91e63" not in source
    assert "self.setStyleSheet(" not in source


def test_view_selector_contract_preserved():
    _app()
    selector = ViewSelector()

    assert selector.objectName() == "LibraryViewSelector"
    assert selector.gallery.isChecked()
    assert selector.gallery.text() == "● 🎮 Gallery"
    assert selector.details.text() == "○ 📋 Details"
    assert selector.compact.text() == "○ 🧱 Compact"


def test_list_view_semantics():
    _app()

    details = DetailsView([])
    compact = CompactView([])

    assert details.objectName() == "LibraryDetailsView"
    assert details.list.objectName() == "LibraryDetailsList"

    assert compact.objectName() == "LibraryCompactView"
    assert compact.list.objectName() == "LibraryCompactList"


def test_game_details_presentation_semantics():
    _app()
    details = GameDetails()

    assert details.objectName() == "LibraryGameDetails"
    assert details.cover.objectName() == "LibraryDetailsCover"
    assert details.title.objectName() == "LibraryDetailsTitle"
    assert (
        details.metadata.objectName()
        == "LibraryDetailsMetadata"
    )
    assert (
        details.description.objectName()
        == "LibraryDetailsDescription"
    )
    assert (
        details.profile.objectName()
        == "LibraryLaunchProfile"
    )
    assert (
        details.favorite_button.objectName()
        == "LibraryFavoriteAction"
    )
    assert (
        details.collection_button.objectName()
        == "LibraryCollectionAction"
    )
    assert (
        details.launch_button.objectName()
        == "LibraryLaunchAction"
    )
    assert (
        details.stop_button.objectName()
        == "LibraryStopAction"
    )
    assert (
        details.launch_status.objectName()
        == "LibraryLaunchStatus"
    )

    assert details.launch_button.text() == "▶ Launch Game"
    assert details.stop_button.text() == "■ Stop Game"
    assert not details.launch_button.isEnabled()
    assert not details.stop_button.isEnabled()


def test_presentation_resolution_contract_preserved():
    source = Path(
        "ui/library/details/game_details.py"
    ).read_text()

    assert "self.presentation_resolver_provider()" in source
    assert "presentation = resolver.resolve(" in source
    assert "shader = presentation.shader" in source
    assert "overlay = presentation.overlay" in source
    assert '"Visual Presentation Unavailable"' in source


def test_library_search_has_professional_desktop_size():
    from ui.library.widgets.library_toolbar import (
        LibraryToolbar,
    )

    toolbar = LibraryToolbar()

    assert (
        toolbar.search.objectName()
        == "LibrarySearch"
    )
    assert (
        toolbar.search.minimumWidth()
        == 180
    )
    assert (
        toolbar.search.maximumWidth()
        == 300
    )
    assert (
        toolbar.search.minimumHeight()
        >= 38
    )


def test_library_search_is_compact_and_does_not_crowd_system_filter():
    from PyQt6.QtWidgets import QApplication

    from ui.library.widgets.library_toolbar import (
        LibraryToolbar,
    )

    app = QApplication.instance() or QApplication([])

    toolbar = LibraryToolbar()

    toolbar.resize(
        1400,
        80,
    )

    toolbar.show()
    app.processEvents()

    assert (
        toolbar.search.minimumWidth()
        == 180
    )

    assert (
        toolbar.search.maximumWidth()
        == 300
    )

    assert (
        toolbar.search.width()
        <= 340
    )

    gap = (
        toolbar.system_filter.x()
        - (
            toolbar.search.x()
            + toolbar.search.width()
        )
    )

    assert gap >= 18

    toolbar.close()

def test_library_view_selector_labels_have_full_text_clearance():
    from PyQt6.QtWidgets import QApplication

    from ui.library.widgets.view_selector import (
        ViewSelector,
    )

    app = QApplication.instance() or QApplication([])

    selector = ViewSelector()

    selector.show()
    app.processEvents()

    for button in (
        selector.gallery,
        selector.details,
        selector.compact,
    ):
        text_width = (
            button.fontMetrics()
            .horizontalAdvance(
                button.text()
            )
        )

        assert (
            button.minimumWidth()
            >= text_width + 20
        )

        assert (
            button.width()
            >= text_width + 20
        )

    selector.close()


def test_library_toolbar_rows_fit_inside_normal_window_width():
    from PyQt6.QtWidgets import QApplication

    from ui.library.widgets.library_toolbar import (
        LibraryToolbar,
    )

    app = QApplication.instance() or QApplication([])

    for width in (
        900,
        1050,
        1168,
        1200,
        1400,
    ):
        toolbar = LibraryToolbar()

        toolbar.resize(
            width,
            110,
        )

        toolbar.show()
        app.processEvents()

        assert (
            toolbar.search.x()
            + toolbar.search.width()
            <= toolbar.width()
        )

        assert (
            toolbar.system_filter.x()
            + toolbar.system_filter.width()
            <= toolbar.width()
        )

        assert (
            toolbar.view_selector.x()
            + toolbar.view_selector.width()
            <= toolbar.width()
        )

        for button in (
            toolbar.view_selector.gallery,
            toolbar.view_selector.details,
            toolbar.view_selector.compact,
        ):
            text_width = (
                button.fontMetrics()
                .horizontalAdvance(
                    button.text()
                )
            )

            assert (
                button.width()
                >= text_width + 20
            )

        toolbar.close()



def test_library_toolbar_action_row_is_visually_contiguous():
    from PyQt6.QtWidgets import QApplication

    from ui.library.widgets.library_toolbar import (
        LibraryToolbar,
    )

    app = QApplication.instance() or QApplication([])

    toolbar = LibraryToolbar()
    toolbar.resize(1168, 110)
    toolbar.show()
    app.processEvents()

    selector = toolbar.view_selector
    random_button = toolbar.random_button
    refresh_button = toolbar.refresh_button
    bulk_button = toolbar.bulk_import_button
    status = toolbar.refresh_status

    assert (
        random_button.x()
        > selector.x() + selector.width()
    )

    assert (
        refresh_button.x()
        > random_button.x()
    )

    assert (
        bulk_button.x()
        > refresh_button.x()
    )

    # No invisible fixed-width status block may separate
    # Refresh Library from Bulk Import.
    refresh_to_bulk_gap = (
        bulk_button.x()
        - (
            refresh_button.x()
            + refresh_button.width()
        )
    )

    assert 0 <= refresh_to_bulk_gap <= 12

    # Status feedback follows the visible actions and absorbs
    # any remaining row width.
    assert status.x() >= (
        bulk_button.x()
        + bulk_button.width()
    )

    assert status.minimumWidth() == 0

    toolbar.close()
