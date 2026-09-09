from pathlib import Path
from types import SimpleNamespace

import pytest

from PyQt6.QtGui import (
    QColor,
    QImage,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox,
)

from services.presentation.service import (
    NativeVisualInstallStatus,
)
from ui.pages.visuals_page import (
    NativeVisualsPage,
)


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()

    if instance is None:
        instance = QApplication([])

    return instance


def make_status(
    tmp_path,
    *,
    state=NativeVisualInstallStatus.NOT_INSTALLED,
    display_name="Nintendo NES — RetroVault Classic",
    asset_id="rvv.overlay.nes.classic",
    preview=True,
):
    package = (
        tmp_path
        / asset_id.replace(".", "_")
    )

    package.mkdir(
        parents=True,
        exist_ok=True,
    )

    descriptor = (
        package
        / "visual.cfg"
    )

    descriptor.write_text(
        'overlays = "1"\n',
        encoding="utf-8",
    )

    source_files = [
        descriptor
    ]

    if preview:
        image_path = (
            package
            / "preview.png"
        )

        image = QImage(
            32,
            24,
            QImage.Format.Format_ARGB32,
        )

        image.fill(
            QColor("red")
        )

        assert image.save(
            str(image_path)
        )

        source_files.append(
            image_path
        )

    asset = SimpleNamespace(
        id=asset_id,
        display_name=display_name,
        asset_type=SimpleNamespace(
            value="overlay"
        ),
        source=SimpleNamespace(
            value="rvv_native"
        ),
        reference=(
            "retro-vault://overlays/"
            "retrovault/nes/classic/"
            "RetroVault_NES_Classic.cfg"
        ),
        author="RetroVault",
        attribution=(
            "Original RetroVault bezel composition."
        ),
    )

    deployment = SimpleNamespace(
        source_files=tuple(
            source_files
        ),
        destination_descriptor=(
            tmp_path
            / "runtime"
            / "visual.cfg"
        ),
    )

    return SimpleNamespace(
        asset=asset,
        status=state,
        deployment=deployment,
    )


class FakeNativeVisualService:
    def __init__(
        self,
        statuses,
    ):
        self.status_by_id = {
            status.asset.id: status
            for status in statuses
        }

        self.install_calls = []

    def native_assets(self):
        return tuple(
            status.asset
            for status in (
                self.status_by_id.values()
            )
        )

    def status(
        self,
        asset_id,
    ):
        return self.status_by_id[
            asset_id
        ]

    def install(
        self,
        asset_id,
    ):
        self.install_calls.append(
            asset_id
        )

        old = self.status_by_id[
            asset_id
        ]

        new = SimpleNamespace(
            asset=old.asset,
            status=(
                NativeVisualInstallStatus.CURRENT
            ),
            deployment=old.deployment,
        )

        self.status_by_id[
            asset_id
        ] = new

        return new


def test_page_lists_curated_native_assets(
    app,
    tmp_path,
):
    status = make_status(
        tmp_path
    )

    page = NativeVisualsPage(
        native_visual_service=(
            FakeNativeVisualService(
                [status]
            )
        )
    )

    assert page.visual_list.count() == 1

    assert (
        "Nintendo NES — RetroVault Classic"
        in page.visual_list.item(0).text()
    )

    assert (
        "Not installed"
        in page.visual_list.item(0).text()
    )

    assert page.count_label.text() == (
        "1 RetroVault visual"
    )


def test_page_shows_retro_vault_metadata(
    app,
    tmp_path,
):
    status = make_status(
        tmp_path
    )

    page = NativeVisualsPage(
        native_visual_service=(
            FakeNativeVisualService(
                [status]
            )
        )
    )

    page.visual_list.setCurrentRow(
        0
    )

    app.processEvents()

    assert page.name_value.text() == (
        "Nintendo NES — RetroVault Classic"
    )

    assert page.source_value.text() == (
        "RetroVault Visuals"
    )

    assert page.type_value.text() == (
        "Overlay"
    )

    assert page.author_value.text() == (
        "RetroVault"
    )

    assert page.install_status_value.text() == (
        "Not installed"
    )

    assert page.reference_value.text().startswith(
        "retro-vault://overlays/"
    )


def test_native_preview_uses_authoritative_source_package(
    app,
    tmp_path,
):
    status = make_status(
        tmp_path,
        preview=True,
    )

    page = NativeVisualsPage(
        native_visual_service=(
            FakeNativeVisualService(
                [status]
            )
        )
    )

    page.visual_list.setCurrentRow(
        0
    )

    app.processEvents()

    assert page.preview.pixmap() is not None
    assert not page.preview.pixmap().isNull()


@pytest.mark.parametrize(
    (
        "state",
        "status_text",
        "button_text",
        "enabled",
    ),
    (
        (
            NativeVisualInstallStatus.NOT_INSTALLED,
            "Not installed",
            "Install",
            True,
        ),
        (
            NativeVisualInstallStatus.OUTDATED,
            "Update available",
            "Update",
            True,
        ),
        (
            NativeVisualInstallStatus.CURRENT,
            "Installed",
            "Installed",
            False,
        ),
    ),
)
def test_installation_states_are_user_facing(
    app,
    tmp_path,
    state,
    status_text,
    button_text,
    enabled,
):
    status = make_status(
        tmp_path,
        state=state,
        asset_id=(
            "rvv.overlay.test."
            + state.value
        ),
    )

    page = NativeVisualsPage(
        native_visual_service=(
            FakeNativeVisualService(
                [status]
            )
        )
    )

    page.visual_list.setCurrentRow(
        0
    )

    app.processEvents()

    assert (
        page.install_status_value.text()
        == status_text
    )

    assert (
        page.install_button.text()
        == button_text
    )

    assert (
        page.install_button.isEnabled()
        is enabled
    )


def test_install_requires_explicit_confirmation(
    app,
    tmp_path,
    monkeypatch,
):
    status = make_status(
        tmp_path
    )

    service = FakeNativeVisualService(
        [status]
    )

    page = NativeVisualsPage(
        native_visual_service=service
    )

    page.visual_list.setCurrentRow(
        0
    )

    app.processEvents()

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: (
            QMessageBox.StandardButton.No
        ),
    )

    page.install_button.click()

    app.processEvents()

    assert service.install_calls == []

    assert page.status_label.text() == (
        "Install cancelled."
    )


def test_confirmed_install_calls_native_service_and_refreshes(
    app,
    tmp_path,
    monkeypatch,
):
    status = make_status(
        tmp_path
    )

    service = FakeNativeVisualService(
        [status]
    )

    page = NativeVisualsPage(
        native_visual_service=service
    )

    page.visual_list.setCurrentRow(
        0
    )

    app.processEvents()

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: (
            QMessageBox.StandardButton.Yes
        ),
    )

    page.install_button.click()

    app.processEvents()

    assert service.install_calls == [
        "rvv.overlay.nes.classic"
    ]

    assert page.install_status_value.text() == (
        "Installed"
    )

    assert page.install_button.text() == (
        "Installed"
    )

    assert not page.install_button.isEnabled()

    assert page.status_label.text() == (
        "Installed "
        "Nintendo NES — RetroVault Classic."
    )


def test_refresh_uses_service_boundary_not_filesystem_scan():
    source = (
        __import__(
            "inspect"
        ).getsource(
            NativeVisualsPage.refresh_visuals
        )
    )

    assert "native_assets()" in source
    assert ".status(" in source
    assert "rglob" not in source
    assert "iterdir" not in source


def test_visual_details_are_vertically_scrollable(
    app,
    tmp_path,
):
    from PyQt6.QtWidgets import QScrollArea

    status = make_status(
        tmp_path,
        state=NativeVisualInstallStatus.CURRENT,
    )

    page = NativeVisualsPage(
        native_visual_service=(
            FakeNativeVisualService(
                [status]
            )
        ),
    )

    page.resize(
        900,
        600,
    )
    page.show()
    app.processEvents()

    assert isinstance(
        page.details_scroll,
        QScrollArea,
    )

    assert (
        page.details_scroll.widgetResizable()
    )

    assert (
        page.details_scroll.verticalScrollBar()
        .maximum()
        > 0
    )

    assert (
        page.details_scroll.widget()
        is not None
    )

    page.close()



def test_page_reuses_existing_presentation_assignment_boundary():
    source = (
        __import__(
            "inspect"
        ).getsource(
            NativeVisualsPage
        )
    )

    assert "PresentationStore(" not in source
    assert ".assign_default_overlay(" in source
    assert ".assign_system_overlay(" in source
    assert ".assign_game_overlay(" in source


def test_existing_overlays_page_remains_separate():
    source = Path(
        "ui/pages/overlays_page.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "NativeVisualService" not in source
    assert "NativeVisualsPage" not in source


def test_main_window_registers_separate_retro_vault_visuals_page():
    source = Path(
        "ui/main_window.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "from ui.pages.visuals_page "
        "import NativeVisualsPage"
        in source
    )

    assert (
        'self.pages.add_page(\n'
        '            "RetroVault Visuals",\n'
        '            NativeVisualsPage(\n'
        in source
    )

    assert (
        "presentation_store=(\n"
        "                    presentation_store"
        in source
    )

    assert (
        "current_game_provider=(\n"
        "                    lambda: ("
        in source
    )

    assert (
        'self.pages.add_page(\n'
        '            "Overlays",'
        in source
    )


def test_page_title_distinguishes_curated_native_collection(
    app,
    tmp_path,
):
    status = make_status(
        tmp_path
    )

    page = NativeVisualsPage(
        native_visual_service=(
            FakeNativeVisualService(
                [status]
            )
        )
    )

    assert page.title_label.text() == (
        "RetroVault Visuals"
    )

    assert page.collection_label.text() == (
        "RetroVault Collection"
    )

    assert (
        "Curated visual presentations"
        in page.subtitle_label.text()
    )


def _assignment_game(
    tmp_path,
    *,
    rvdb_platform_id="platform.nintendo.nes",
):
    from services.library.models import Game

    return Game(
        name="Duck Tales 2",
        platform="NES",
        year=1993,
        genre="Platformer",
        core="nestopia",
        rom=str(
            tmp_path / "Duck Tales 2 (U).nes"
        ),
        rvdb_platform_id=rvdb_platform_id,
    )


def test_native_assignment_buttons_require_current_install(
    app,
    tmp_path,
):
    from services.presentation import PresentationStore

    status = make_status(
        tmp_path,
        state=NativeVisualInstallStatus.NOT_INSTALLED,
    )

    store = PresentationStore(
        tmp_path / "presentation-state.json"
    )

    game = _assignment_game(
        tmp_path
    )

    page = NativeVisualsPage(
        native_visual_service=(
            FakeNativeVisualService(
                [status]
            )
        ),
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.visual_list.setCurrentRow(0)
    app.processEvents()

    assert not page.default_button.isEnabled()
    assert not page.system_button.isEnabled()
    assert not page.game_button.isEnabled()


def test_native_current_visual_enables_assignment_controls(
    app,
    tmp_path,
):
    from services.presentation import PresentationStore

    status = make_status(
        tmp_path,
        state=NativeVisualInstallStatus.CURRENT,
    )

    store = PresentationStore(
        tmp_path / "presentation-state.json"
    )

    game = _assignment_game(
        tmp_path
    )

    page = NativeVisualsPage(
        native_visual_service=(
            FakeNativeVisualService(
                [status]
            )
        ),
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.visual_list.setCurrentRow(0)
    app.processEvents()

    assert page.default_button.isEnabled()
    assert page.system_button.isEnabled()
    assert page.game_button.isEnabled()


def test_native_default_assignment_persists_portable_reference(
    app,
    tmp_path,
):
    from services.presentation import PresentationStore

    status = make_status(
        tmp_path,
        state=NativeVisualInstallStatus.CURRENT,
    )

    store = PresentationStore(
        tmp_path / "presentation-state.json"
    )

    page = NativeVisualsPage(
        native_visual_service=(
            FakeNativeVisualService(
                [status]
            )
        ),
        presentation_store=store,
    )

    page.visual_list.setCurrentRow(0)
    app.processEvents()

    page.default_button.click()
    app.processEvents()

    assert (
        store.load()["default"].overlay
        == status.asset.reference
    )

    assert status.asset.reference.startswith(
        "retro-vault://overlays/"
    )


def test_native_system_assignment_uses_canonical_rvdb_platform(
    app,
    tmp_path,
):
    from services.presentation import PresentationStore

    status = make_status(
        tmp_path,
        state=NativeVisualInstallStatus.CURRENT,
    )

    store = PresentationStore(
        tmp_path / "presentation-state.json"
    )

    game = _assignment_game(
        tmp_path
    )

    page = NativeVisualsPage(
        native_visual_service=(
            FakeNativeVisualService(
                [status]
            )
        ),
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.visual_list.setCurrentRow(0)
    app.processEvents()

    page.system_button.click()
    app.processEvents()

    assert (
        store.load()["systems"][
            "platform.nintendo.nes"
        ].overlay
        == status.asset.reference
    )


def test_native_game_assignment_uses_game_identity(
    app,
    tmp_path,
):
    from services.library.state import game_identity
    from services.presentation import PresentationStore

    status = make_status(
        tmp_path,
        state=NativeVisualInstallStatus.CURRENT,
    )

    store = PresentationStore(
        tmp_path / "presentation-state.json"
    )

    game = _assignment_game(
        tmp_path
    )

    page = NativeVisualsPage(
        native_visual_service=(
            FakeNativeVisualService(
                [status]
            )
        ),
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.visual_list.setCurrentRow(0)
    app.processEvents()

    page.game_button.click()
    app.processEvents()

    identity = game_identity(
        game
    )

    assert (
        store.load()["games"][identity].overlay
        == status.asset.reference
    )


def test_native_system_assignment_rejects_missing_canonical_id(
    app,
    tmp_path,
):
    from services.presentation import PresentationStore

    status = make_status(
        tmp_path,
        state=NativeVisualInstallStatus.CURRENT,
    )

    store = PresentationStore(
        tmp_path / "presentation-state.json"
    )

    game = _assignment_game(
        tmp_path,
        rvdb_platform_id="",
    )

    page = NativeVisualsPage(
        native_visual_service=(
            FakeNativeVisualService(
                [status]
            )
        ),
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.visual_list.setCurrentRow(0)
    app.processEvents()

    page.system_button.click()
    app.processEvents()

    assert store.load()["systems"] == {}

    assert page.status_label.text() == (
        "The selected game does not have "
        "a canonical RVDB system identity."
    )


def test_native_assignment_preserves_other_presentation_fields(
    app,
    tmp_path,
):
    from services.presentation import (
        PresentationProfile,
        PresentationStore,
    )

    status = make_status(
        tmp_path,
        state=NativeVisualInstallStatus.CURRENT,
    )

    store = PresentationStore(
        tmp_path / "presentation-state.json"
    )

    store.save(
        default=PresentationProfile(
            shader="/existing/default.slangp",
            artwork="/existing/default.png",
        ),
        systems={},
        games={},
    )

    page = NativeVisualsPage(
        native_visual_service=(
            FakeNativeVisualService(
                [status]
            )
        ),
        presentation_store=store,
    )

    page.visual_list.setCurrentRow(0)
    app.processEvents()

    page.default_button.click()
    app.processEvents()

    profile = store.load()["default"]

    assert profile.shader == (
        "/existing/default.slangp"
    )
    assert profile.artwork == (
        "/existing/default.png"
    )
    assert profile.overlay == (
        status.asset.reference
    )


def test_main_window_injects_shared_assignment_context_into_visuals_page():
    source = Path(
        "ui/main_window.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "NativeVisualsPage(\n"
        "                presentation_store=("
        in source
    )

    assert (
        "library_page\n"
        "                        .details\n"
        "                        .current_game"
        in source
    )
