import pytest

from PyQt6.QtWidgets import (
    QApplication,
    QInputDialog,
    QMessageBox,
)

from services.library.models import Game
from ui.pages.playlists_page import (
    PlaylistsPage,
)


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()

    if instance is None:
        instance = QApplication([])

    return instance


class FakeController:
    def __init__(self):
        self.collections = {
            "NES": [],
        }

    def collection_names(self):
        return list(
            self.collections
        )

    def collection_games(
        self,
        name,
    ):
        return list(
            self.collections[name]
        )

    def create_collection(
        self,
        name,
    ):
        normalized = name.strip()

        if not normalized:
            raise ValueError(
                "Collection name cannot be empty."
            )

        if normalized in self.collections:
            raise ValueError(
                "Collection already exists."
            )

        self.collections[normalized] = []

        return normalized

    def rename_collection(
        self,
        current,
        new,
    ):
        normalized = new.strip()

        if not normalized:
            raise ValueError(
                "Collection name cannot be empty."
            )

        games = self.collections.pop(
            current
        )
        self.collections[normalized] = games

        return normalized

    def delete_collection(
        self,
        name,
    ):
        del self.collections[name]


def make_game(
    name="Duck Tales 2",
):
    return Game(
        name=name,
        platform="NES",
        year=1993,
        genre="Platformer",
        core="fceumm",
        rom=f"/roms/{name}.nes",
    )


def test_page_lists_existing_collections(
    app,
):
    page = PlaylistsPage(
        FakeController()
    )

    assert page.collection_list.count() == 1
    assert (
        page.collection_list.item(0).text()
        == "NES"
    )
    assert page.selected_collection() == "NES"


def test_page_displays_selected_collection_games(
    app,
):
    controller = FakeController()
    controller.collections["NES"] = [
        make_game()
    ]

    page = PlaylistsPage(controller)

    assert page.collection_title.text() == "NES"
    assert page.game_list.count() == 1
    assert page.game_list.item(0).text() == (
        "Duck Tales 2 — NES"
    )
    assert page.status_label.text() == "1 game"


def test_page_creates_collection(
    app,
    monkeypatch,
):
    controller = FakeController()
    page = PlaylistsPage(controller)

    monkeypatch.setattr(
        QInputDialog,
        "getText",
        lambda *args, **kwargs: (
            "Weekend",
            True,
        ),
    )

    page.create_collection()

    assert "Weekend" in (
        controller.collections
    )
    assert (
        page.selected_collection()
        == "Weekend"
    )


def test_page_rename_preserves_games(
    app,
    monkeypatch,
):
    controller = FakeController()
    game = make_game()
    controller.collections["NES"] = [
        game
    ]

    page = PlaylistsPage(controller)

    monkeypatch.setattr(
        QInputDialog,
        "getText",
        lambda *args, **kwargs: (
            "Nintendo",
            True,
        ),
    )

    page.rename_collection()

    assert "NES" not in controller.collections
    assert controller.collections[
        "Nintendo"
    ] == [game]
    assert (
        page.selected_collection()
        == "Nintendo"
    )


def test_page_delete_requires_confirmation(
    app,
    monkeypatch,
):
    controller = FakeController()
    page = PlaylistsPage(controller)

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: (
            QMessageBox.StandardButton.No
        ),
    )

    page.delete_collection()

    assert "NES" in controller.collections


def test_page_deletes_confirmed_collection(
    app,
    monkeypatch,
):
    controller = FakeController()
    page = PlaylistsPage(controller)

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: (
            QMessageBox.StandardButton.Yes
        ),
    )

    page.delete_collection()

    assert controller.collections == {}
    assert page.collection_list.count() == 0
    assert page.game_list.count() == 0
    assert not page.rename_button.isEnabled()
    assert not page.delete_button.isEnabled()


def test_page_reports_empty_collection(
    app,
):
    page = PlaylistsPage(
        FakeController()
    )

    assert page.status_label.text() == (
        "0 games"
    )


def test_page_handles_invalid_create(
    app,
    monkeypatch,
):
    controller = FakeController()
    page = PlaylistsPage(controller)
    warnings = []

    monkeypatch.setattr(
        QInputDialog,
        "getText",
        lambda *args, **kwargs: (
            " ",
            True,
        ),
    )

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: (
            warnings.append(args[2])
        ),
    )

    page.create_collection()

    assert warnings == [
        "Collection name cannot be empty."
    ]
    assert page.collection_list.count() == 1


def test_playlists_page_uses_controller_boundary():
    source = (
        __import__(
            "inspect"
        ).getsource(
            PlaylistsPage
        )
    )

    assert "CollectionStore" not in source
    assert "collections.json" not in source
