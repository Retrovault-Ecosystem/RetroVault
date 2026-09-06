from types import SimpleNamespace

import pytest

from PyQt6.QtGui import (
    QColor,
    QImage,
)
from PyQt6.QtWidgets import (
    QApplication,
)

from ui.pages.overlays_page import (
    OverlaysPage,
)


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()

    if instance is None:
        instance = QApplication([])

    return instance


class FakeLoader:
    def __init__(
        self,
        directory,
    ):
        self.directory = directory

    def load(self):
        return {
            "paths": {
                "overlays": {
                    "directory": str(
                        self.directory
                    ),
                },
            },
        }


class FakeService:
    def __init__(
        self,
        overlays=None,
    ):
        self.overlays = list(
            overlays or []
        )
        self.scans = 0

    def scan(self):
        self.scans += 1
        return list(
            self.overlays
        )


def make_overlay(
    tmp_path,
    *,
    name="NES",
    ready=True,
    image_paths=(),
):
    missing = (
        ()
        if ready
        else (
            tmp_path / "missing.png",
        )
    )

    return SimpleNamespace(
        name=name,
        config_path=(
            tmp_path / f"{name}.cfg"
        ),
        relative_config=(
            __import__(
                "pathlib"
            ).Path(
                f"{name}.cfg"
            )
        ),
        image_paths=tuple(
            image_paths
        ),
        missing_images=missing,
        ready=ready,
        image_count=len(
            image_paths
        ),
    )


def test_page_shows_effective_directory(
    app,
    tmp_path,
):
    page = OverlaysPage(
        config_loader=FakeLoader(
            tmp_path
        ),
        overlay_service=FakeService(),
    )

    assert page.path_label.text() == (
        str(tmp_path)
    )


def test_empty_directory_has_clear_state(
    app,
    tmp_path,
):
    page = OverlaysPage(
        config_loader=FakeLoader(
            tmp_path
        ),
        overlay_service=FakeService(),
    )

    assert page.overlay_list.count() == 0
    assert page.count_label.text() == (
        "0 installed overlays"
    )
    assert page.status_label.text() == (
        "No installed overlay descriptors "
        "were found in this directory."
    )


def test_missing_directory_has_clear_state(
    app,
    tmp_path,
):
    missing = tmp_path / "missing"

    page = OverlaysPage(
        config_loader=FakeLoader(
            missing
        ),
        overlay_service=FakeService(),
    )

    assert page.status_label.text() == (
        "The configured overlay directory "
        "does not exist."
    )


def test_page_lists_discovered_overlays(
    app,
    tmp_path,
):
    service = FakeService(
        [
            make_overlay(
                tmp_path,
                name="Arcade",
            ),
            make_overlay(
                tmp_path,
                name="NES",
            ),
        ]
    )

    page = OverlaysPage(
        config_loader=FakeLoader(
            tmp_path
        ),
        overlay_service=service,
    )

    assert page.overlay_list.count() == 2
    assert (
        page.overlay_list.item(0).text()
        == "Arcade"
    )
    assert (
        page.overlay_list.item(1).text()
        == "NES"
    )
    assert page.count_label.text() == (
        "2 installed overlays"
    )


def test_selecting_ready_overlay_shows_details(
    app,
    tmp_path,
):
    overlay = make_overlay(
        tmp_path,
        name="NES",
    )

    page = OverlaysPage(
        config_loader=FakeLoader(
            tmp_path
        ),
        overlay_service=FakeService(
            [overlay]
        ),
    )

    page.overlay_list.setCurrentRow(0)
    app.processEvents()

    assert page.name_value.text() == "NES"
    assert page.config_value.text() == (
        "NES.cfg"
    )
    assert page.images_value.text() == "0"
    assert page.missing_value.text() == "0"
    assert page.readiness_value.text() == (
        "Ready"
    )


def test_missing_assets_are_reported(
    app,
    tmp_path,
):
    overlay = make_overlay(
        tmp_path,
        name="Broken",
        ready=False,
    )

    page = OverlaysPage(
        config_loader=FakeLoader(
            tmp_path
        ),
        overlay_service=FakeService(
            [overlay]
        ),
    )

    page.overlay_list.setCurrentRow(0)
    app.processEvents()

    assert page.readiness_value.text() == (
        "Missing assets"
    )
    assert page.missing_value.text() == "1"


def test_refresh_rescans_and_clears_stale_details(
    app,
    tmp_path,
):
    service = FakeService(
        [
            make_overlay(
                tmp_path
            )
        ]
    )

    page = OverlaysPage(
        config_loader=FakeLoader(
            tmp_path
        ),
        overlay_service=service,
    )

    page.overlay_list.setCurrentRow(0)
    app.processEvents()

    service.overlays = []
    page.refresh_button.click()
    app.processEvents()

    assert service.scans == 2
    assert page.overlay_list.count() == 0
    assert page.name_value.text() == (
        "Select an overlay"
    )


def test_valid_first_image_is_previewed(
    app,
    tmp_path,
):
    image_path = tmp_path / "preview.png"

    image = QImage(
        20,
        20,
        QImage.Format.Format_ARGB32,
    )
    image.fill(
        QColor("red")
    )
    assert image.save(
        str(image_path)
    )

    overlay = make_overlay(
        tmp_path,
        image_paths=(
            image_path,
        ),
    )

    page = OverlaysPage(
        config_loader=FakeLoader(
            tmp_path
        ),
        overlay_service=FakeService(
            [overlay]
        ),
    )

    page.overlay_list.setCurrentRow(0)
    app.processEvents()

    assert page.preview.pixmap() is not None
    assert not page.preview.pixmap().isNull()


def test_page_uses_overlay_service_boundary():
    source = (
        __import__(
            "inspect"
        ).getsource(
            OverlaysPage
        )
    )

    assert "rglob" not in source
    assert "read_text" not in source


def assignment_game(
    tmp_path,
    *,
    rvdb_platform_id="platform.nintendo.nes",
):
    from services.library.models import Game

    rom = tmp_path / "Duck Tales 2 (U).nes"

    return Game(
        name="Duck Tales 2",
        platform="NES",
        year=1993,
        genre="Platformer",
        core="nestopia",
        rom=str(rom),
        rvdb_platform_id=rvdb_platform_id,
    )


def test_assignment_buttons_require_ready_selected_overlay(
    app,
    tmp_path,
):
    from services.presentation import PresentationStore

    broken = make_overlay(
        tmp_path,
        name="Broken",
        ready=False,
    )

    store = PresentationStore(
        tmp_path / "presentation-state.json"
    )

    game = assignment_game(
        tmp_path
    )

    page = OverlaysPage(
        config_loader=FakeLoader(
            tmp_path
        ),
        overlay_service=FakeService(
            [broken]
        ),
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.overlay_list.setCurrentRow(0)
    app.processEvents()

    assert not page.default_button.isEnabled()
    assert not page.system_button.isEnabled()
    assert not page.game_button.isEnabled()


def test_default_overlay_assignment_persists_selected_descriptor(
    app,
    tmp_path,
):
    from services.presentation import PresentationStore

    overlay = make_overlay(
        tmp_path,
        name="Default",
        ready=True,
    )

    store = PresentationStore(
        tmp_path / "presentation-state.json"
    )

    page = OverlaysPage(
        config_loader=FakeLoader(
            tmp_path
        ),
        overlay_service=FakeService(
            [overlay]
        ),
        presentation_store=store,
    )

    page.overlay_list.setCurrentRow(0)
    app.processEvents()

    assert page.default_button.isEnabled()

    page.default_button.click()
    app.processEvents()

    data = store.load()

    expected = str(
        overlay.config_path.expanduser().resolve(
            strict=False
        )
    )

    assert data["default"].overlay == expected

    assert page.status_label.text() == (
        "Assigned selected overlay as "
        "RetroVault default."
    )


def test_system_overlay_assignment_uses_rvdb_platform_id(
    app,
    tmp_path,
):
    from services.presentation import PresentationStore

    overlay = make_overlay(
        tmp_path,
        name="NES",
        ready=True,
    )

    store = PresentationStore(
        tmp_path / "presentation-state.json"
    )

    game = assignment_game(
        tmp_path
    )

    page = OverlaysPage(
        config_loader=FakeLoader(
            tmp_path
        ),
        overlay_service=FakeService(
            [overlay]
        ),
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.overlay_list.setCurrentRow(0)
    app.processEvents()

    assert page.system_button.isEnabled()

    page.system_button.click()
    app.processEvents()

    data = store.load()

    expected = str(
        overlay.config_path.expanduser().resolve(
            strict=False
        )
    )

    assert (
        data["systems"][
            "platform.nintendo.nes"
        ].overlay
        == expected
    )


def test_game_overlay_assignment_uses_game_identity(
    app,
    tmp_path,
):
    from services.library.state import game_identity
    from services.presentation import PresentationStore

    overlay = make_overlay(
        tmp_path,
        name="Duck Tales",
        ready=True,
    )

    store = PresentationStore(
        tmp_path / "presentation-state.json"
    )

    game = assignment_game(
        tmp_path
    )

    page = OverlaysPage(
        config_loader=FakeLoader(
            tmp_path
        ),
        overlay_service=FakeService(
            [overlay]
        ),
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.overlay_list.setCurrentRow(0)
    app.processEvents()

    assert page.game_button.isEnabled()

    page.game_button.click()
    app.processEvents()

    data = store.load()

    identity = game_identity(
        game
    )

    expected = str(
        overlay.config_path.expanduser().resolve(
            strict=False
        )
    )

    assert data["games"][identity].overlay == expected


def test_system_overlay_assignment_requires_canonical_rvdb_id(
    app,
    tmp_path,
):
    from services.presentation import PresentationStore

    overlay = make_overlay(
        tmp_path,
        name="No ID",
        ready=True,
    )

    store = PresentationStore(
        tmp_path / "presentation-state.json"
    )

    game = assignment_game(
        tmp_path,
        rvdb_platform_id="",
    )

    page = OverlaysPage(
        config_loader=FakeLoader(
            tmp_path
        ),
        overlay_service=FakeService(
            [overlay]
        ),
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.overlay_list.setCurrentRow(0)
    app.processEvents()

    page.system_button.click()
    app.processEvents()

    assert store.load()["systems"] == {}

    assert page.status_label.text() == (
        "The selected game does not have "
        "a canonical RVDB system identity."
    )


def test_overlay_assignment_is_immediately_visible_to_lazy_resolver(
    app,
    tmp_path,
):
    from services.presentation import PresentationStore

    overlay = make_overlay(
        tmp_path,
        name="Immediate",
        ready=True,
    )

    store = PresentationStore(
        tmp_path / "presentation-state.json"
    )

    game = assignment_game(
        tmp_path
    )

    resolver_provider = store.resolver

    before = resolver_provider().resolve(
        game
    )

    assert before.overlay == ""

    page = OverlaysPage(
        config_loader=FakeLoader(
            tmp_path
        ),
        overlay_service=FakeService(
            [overlay]
        ),
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.overlay_list.setCurrentRow(0)
    app.processEvents()

    page.game_button.click()
    app.processEvents()

    after = resolver_provider().resolve(
        game
    )

    expected = str(
        overlay.config_path.expanduser().resolve(
            strict=False
        )
    )

    assert after.overlay == expected


def test_ready_overlay_without_presentation_store_is_not_assignable(
    app,
    tmp_path,
):
    overlay = make_overlay(
        tmp_path,
        name="Ready",
        ready=True,
    )

    page = OverlaysPage(
        config_loader=FakeLoader(
            tmp_path
        ),
        overlay_service=FakeService(
            [overlay]
        ),
    )

    page.overlay_list.setCurrentRow(0)
    app.processEvents()

    assert not page.default_button.isEnabled()
    assert not page.system_button.isEnabled()
    assert not page.game_button.isEnabled()
