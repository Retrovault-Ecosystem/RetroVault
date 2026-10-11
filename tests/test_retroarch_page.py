import json

import pytest
from PyQt6.QtWidgets import QApplication

from services.rvdb import RVDBService
from ui.pages.retroarch_page import RetroArchPage


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()

    if instance is None:
        instance = QApplication([])

    return instance


@pytest.fixture
def service(tmp_path):
    bundle = {
        "nodes": {
            "frontend.retroarch": {
                "id": "frontend.retroarch",
                "type": "frontend",
                "name": "RetroArch",
                "aliases": [],
                "metadata": {},
                "relationships": {
                    "launches_core": [
                        "core.alpha",
                        "core.beta",
                    ]
                },
            },
            "core.alpha": {
                "id": "core.alpha",
                "type": "core",
                "name": "Alpha Core",
                "aliases": [],
                "metadata": {},
                "relationships": {},
            },
            "core.beta": {
                "id": "core.beta",
                "type": "core",
                "name": "Beta Core",
                "aliases": [],
                "metadata": {},
                "relationships": {},
            },
            "platform.alpha": {
                "id": "platform.alpha",
                "type": "platform",
                "name": "Alpha System",
                "aliases": [],
                "metadata": {},
                "relationships": {},
            },
            "compatibility.alpha": {
                "id": "compatibility.alpha",
                "type": "compatibility",
                "name": "Alpha Compatibility",
                "subject": "core.alpha",
                "platform": "platform.alpha",
                "playability": "playable",
                "evidence": [
                    "one",
                    "two",
                ],
                "aliases": [],
                "metadata": {},
                "relationships": {},
            },
        },
        "edges": {
            "frontend.retroarch": {
                "launches_core": [
                    "core.alpha",
                    "core.beta",
                ]
            }
        },
    }

    path = tmp_path / "rvdb.bundle.json"

    path.write_text(
        json.dumps(bundle),
        encoding="utf-8",
    )

    return RVDBService.from_bundle(
        path
    )


def test_retroarch_page_lists_frontend_cores(
    app,
    service,
):
    page = RetroArchPage(
        service
    )

    app.processEvents()

    assert page.core_list.count() == 2

    assert [
        page.core_list.item(
            row
        ).text()
        for row in range(
            page.core_list.count()
        )
    ] == [
        "Alpha Core",
        "Beta Core",
    ]

    assert page.core_count_label.text() == (
        "2 cores"
    )

    assert page.summary_label.text() == (
        "RVDB lists 2 cores for RetroArch."
    )


def test_retroarch_page_shows_core_details(
    app,
    service,
):
    page = RetroArchPage(
        service
    )

    app.processEvents()

    assert page.core_name_label.text() == (
        "Alpha Core"
    )

    assert page.core_id_label.text() == (
        "core.alpha"
    )

    assert page.platforms_value.text() == (
        "Alpha System"
    )

    assert page.playability_value.text() == (
        "playable"
    )

    assert page.evidence_value.text() == "2"

    assert page.frontends_value.text() == (
        "RetroArch"
    )


def test_retroarch_page_changes_selection(
    app,
    service,
):
    page = RetroArchPage(
        service
    )

    page.core_list.setCurrentRow(1)

    app.processEvents()

    assert page.core_name_label.text() == (
        "Beta Core"
    )

    assert page.platforms_value.text() == (
        "No compatibility records."
    )

    assert page.playability_value.text() == (
        "Unknown"
    )

    assert page.evidence_value.text() == "0"

    assert page.frontends_value.text() == (
        "RetroArch"
    )


def test_retroarch_page_handles_missing_service(
    app,
):
    page = RetroArchPage(None)

    app.processEvents()

    assert page.core_list.count() == 0

    assert page.status_label.text() == (
        "RVDB unavailable"
    )

    assert page.core_count_label.text() == (
        "0 cores"
    )


def test_retroarch_page_real_rvdb_contract(
    app,
):
    service = RVDBService.from_bundle(
        "data/rvdb/rvdb.bundle.json"
    )

    page = RetroArchPage(
        service
    )

    app.processEvents()

    assert page.core_list.count() == 7

    names = {
        page.core_list.item(
            row
        ).text()
        for row in range(
            page.core_list.count()
        )
    }

    assert names == {
        "Bsnes",
        "FCEUmm",
        "Genesis Plus GX",
        "MAME",
        "Mesen",
        "Mupen64Plus-Next",
        "Snes9x",
    }

    for row in range(
        page.core_list.count()
    ):
        item = page.core_list.item(row)

        if item.text() == "Bsnes":
            page.core_list.setCurrentRow(
                row
            )
            break
    else:
        raise AssertionError(
            "Bsnes missing from RetroArch page"
        )

    app.processEvents()

    assert page.platforms_value.text() == (
        "Super Nintendo"
    )

    assert page.playability_value.text() == (
        "playable"
    )

    assert page.evidence_value.text() == "3"

    assert page.frontends_value.text() == (
        "RetroArch"
    )


def test_retroarch_details_are_side_by_side(
    app,
    service,
):
    page = RetroArchPage(
        service
    )

    pairs = [
        (
            page.platforms_label,
            page.platforms_value,
            0,
        ),
        (
            page.playability_label,
            page.playability_value,
            1,
        ),
        (
            page.evidence_label,
            page.evidence_value,
            2,
        ),
    ]

    for label, value, row in pairs:
        label_index = (
            page.details_grid.indexOf(
                label
            )
        )

        value_index = (
            page.details_grid.indexOf(
                value
            )
        )

        label_position = (
            page.details_grid
            .getItemPosition(
                label_index
            )
        )

        value_position = (
            page.details_grid
            .getItemPosition(
                value_index
            )
        )

        assert label_position[:2] == (
            row,
            0,
        )

        assert value_position[:2] == (
            row,
            1,
        )

    frontend_label_position = (
        page.frontend_grid
        .getItemPosition(
            page.frontend_grid.indexOf(
                page.frontends_label
            )
        )
    )

    frontend_value_position = (
        page.frontend_grid
        .getItemPosition(
            page.frontend_grid.indexOf(
                page.frontends_value
            )
        )
    )

    assert frontend_label_position[:2] == (
        0,
        0,
    )

    assert frontend_value_position[:2] == (
        0,
        1,
    )


def test_claim_explanations_escape_markup_and_reject_unsafe_links(app, service):
    from services.rvdb.models import RVDBCoreView, RVDBCompatibilityView, RVDBEvidenceView
    page=RetroArchPage(service)
    claim=RVDBCompatibilityView('claim.test','core.test','platform.test','<img src=x>',
        'experimental', notes='<script>bad</script>', evidence=(
            RVDBEvidenceView('<b>source</b>','javascript:alert(1)',''),
            RVDBEvidenceView('Official','https://example.org/evidence','2026-10-10')))
    page._show_core(RVDBCoreView('core.test','Test',(),(),2,(),(claim,)))
    text=page.compatibility_details.toPlainText();html=page.compatibility_details.toHtml()
    assert '<img src=x>' in text and '<script>bad</script>' in text
    assert 'Version: Not specified' in text and 'Checked: Not supplied' in text
    assert 'not local readiness' in text
    assert 'href="javascript:' not in html and '<img src="x"' not in html
    assert 'href="https://example.org/evidence"' in html
    page._show_core(RVDBCoreView('core.test','Test',(),(),0,()))
    assert 'No compatibility records' in page.compatibility_details.toPlainText()
    page._clear_details()
    assert 'Select a core' in page.compatibility_details.toPlainText()
    page.close()
