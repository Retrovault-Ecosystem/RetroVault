from collections import OrderedDict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from services.library.game_variants import (
    CATEGORY_TITLES,
    VariantCategory,
)


_CATEGORY_ORDER = tuple(
    category.value
    for category in VariantCategory
)


class GameEditionLauncher(QDialog):
    """
    Professional RetroVault edition selector.

    A canonical Library entry may represent several physical ROM
    editions. This dialog exposes those editions as semantic groups
    while keeping the normal Library free from duplicate cards.

    The preferred canonical edition is selected by default.
    """


    @staticmethod
    def _category_key(value):
        """
        Normalize A.7 variant category representations to the
        stable internal keys consumed by the grouped launcher.

        A.7 records may contain VariantCategory enum values,
        enum names, raw semantic values, or professional UI titles.
        """

        raw = getattr(
            value,
            "value",
            value,
        )

        raw = str(
            raw or ""
        ).strip()

        normalized = (
            raw.casefold()
            .replace("&", "and")
            .replace("/", " ")
            .replace("_", " ")
            .replace("-", " ")
        )

        normalized = " ".join(
            normalized.split()
        )

        aliases = {
            "standard": "standard",
            "standard edition": "standard",

            "revision": "revision",
            "revisions": "revision",

            "translation": "translation",
            "translations": "translation",
            "translations and languages": "translation",
            "language": "translation",
            "languages": "translation",

            "region": "region",
            "regional": "region",
            "regional edition": "region",
            "regional editions": "region",

            "hack": "hack",
            "hacks": "hack",
            "mod": "hack",
            "mods": "hack",
            "hacks and mods": "hack",

            "prototype": "prototype",
            "prototypes": "prototype",
            "beta": "prototype",
            "betas": "prototype",
            "prototypes and betas": "prototype",

            "unlicensed": "unlicensed",
            "aftermarket": "unlicensed",
            "unlicensed aftermarket": "unlicensed",

            "other": "other",
            "other variant": "other",
            "other variants": "other",
        }

        return aliases.get(
            normalized,
            "other",
        )

    def __init__(
        self,
        game,
        parent=None,
    ):
        super().__init__(parent)

        self.game = game
        self._selected_variant = None
        self._variant_buttons = []

        self.setObjectName(
            "LibraryEditionLauncher"
        )

        self.setWindowTitle(
            "Choose Game Edition"
        )

        self.setModal(True)

        self.setMinimumSize(
            620,
            520,
        )

        self.resize(
            720,
            620,
        )

        self._build_ui()

    @property
    def selected_variant(self):
        return self._selected_variant

    @staticmethod
    def variants_for_game(game):
        variants = list(
            getattr(
                game,
                "variants",
                [],
            )
            or []
        )

        if variants:
            return variants

        return [
            {
                "name": getattr(
                    game,
                    "name",
                    "",
                ),
                "rom": getattr(
                    game,
                    "rom",
                    "",
                ),
                "source": getattr(
                    game,
                    "source",
                    "",
                ),
                "category": (
                    VariantCategory.STANDARD.value
                ),
                "label": "",
                "region": "",
                "language": "",
                "revision": "",
                "preferred": True,
            }
        ]

    @classmethod
    def requires_selection(cls, game):
        return (
            len(
                cls.variants_for_game(
                    game
                )
            )
            > 1
        )

    @classmethod
    def _category_value(cls, variant):
        """
        Return the stable launcher category key for an A.7
        variant record without mutating the canonical record.
        """

        if isinstance(
            variant,
            dict,
        ):
            value = variant.get(
                "category",
                "other",
            )
        else:
            value = getattr(
                variant,
                "category",
                "other",
            )

        return cls._category_key(
            value
        )

    @classmethod
    def grouped_variants(cls, game):
        grouped = OrderedDict(
            (
                category,
                [],
            )
            for category in _CATEGORY_ORDER
        )

        for variant in cls.variants_for_game(
            game
        ):
            grouped[
                cls._category_value(
                    variant
                )
            ].append(
                variant
            )

        return OrderedDict(
            (
                category,
                variants,
            )
            for category, variants
            in grouped.items()
            if variants
        )

    @staticmethod
    def category_title(category):
        try:
            enum_value = VariantCategory(
                category
            )
        except ValueError:
            enum_value = (
                VariantCategory.OTHER
            )

        return CATEGORY_TITLES[
            enum_value
        ]

    @staticmethod
    def edition_label(variant):
        labels = []

        region = str(
            variant.get(
                "region",
                "",
            )
            or ""
        ).strip()

        language = str(
            variant.get(
                "language",
                "",
            )
            or ""
        ).strip()

        revision = str(
            variant.get(
                "revision",
                "",
            )
            or ""
        ).strip()

        explicit_label = str(
            variant.get(
                "label",
                "",
            )
            or ""
        ).strip()

        for value in (
            region,
            language,
            revision,
        ):
            if (
                value
                and value not in labels
            ):
                labels.append(value)

        if (
            explicit_label
            and explicit_label not in labels
        ):
            labels.append(
                explicit_label
            )

        if labels:
            return " • ".join(labels)

        name = str(
            variant.get(
                "name",
                "",
            )
            or ""
        ).strip()

        if name:
            return name

        return "Game Edition"

    @staticmethod
    def edition_detail(variant):
        rom = str(
            variant.get(
                "rom",
                "",
            )
            or ""
        ).strip()

        if not rom:
            return ""

        return rom.rsplit(
            "/",
            1,
        )[-1]

    def _build_ui(self):
        root = QVBoxLayout(self)

        root.setContentsMargins(
            24,
            22,
            24,
            22,
        )

        root.setSpacing(14)

        eyebrow = QLabel(
            "RETROVAULT GAME EDITIONS"
        )

        eyebrow.setObjectName(
            "LibraryEditionEyebrow"
        )

        root.addWidget(eyebrow)

        title = QLabel(
            getattr(
                self.game,
                "canonical_title",
                "",
            )
            or getattr(
                self.game,
                "name",
                "Game",
            )
        )

        title.setObjectName(
            "LibraryEditionTitle"
        )

        title.setWordWrap(True)

        root.addWidget(title)

        variants = (
            self.variants_for_game(
                self.game
            )
        )

        subtitle = QLabel(
            (
                f"{len(variants)} playable "
                f"{'edition' if len(variants) == 1 else 'editions'} "
                "available. Choose the version you want RetroVault "
                "to launch."
            )
        )

        subtitle.setObjectName(
            "LibraryEditionSubtitle"
        )

        subtitle.setWordWrap(True)

        root.addWidget(subtitle)

        scroll = QScrollArea()

        scroll.setObjectName(
            "LibraryEditionScroll"
        )

        scroll.setWidgetResizable(True)

        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        content = QWidget()

        content.setObjectName(
            "LibraryEditionContent"
        )

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            0,
            4,
            8,
            4,
        )

        content_layout.setSpacing(14)

        self.button_group = QButtonGroup(
            self
        )

        self.button_group.setExclusive(
            True
        )

        preferred_button = None
        first_button = None

        for category, editions in (
            self.grouped_variants(
                self.game
            ).items()
        ):
            group = QFrame()

            group.setObjectName(
                "LibraryEditionGroup"
            )

            group_layout = QVBoxLayout(
                group
            )

            group_layout.setContentsMargins(
                16,
                14,
                16,
                14,
            )

            group_layout.setSpacing(8)

            heading = QLabel(
                self.category_title(
                    category
                )
            )

            heading.setObjectName(
                "LibraryEditionGroupTitle"
            )

            group_layout.addWidget(
                heading
            )

            for variant in editions:
                row = QFrame()

                row.setObjectName(
                    "LibraryEditionRow"
                )

                row_layout = QVBoxLayout(
                    row
                )

                row_layout.setContentsMargins(
                    12,
                    9,
                    12,
                    9,
                )

                row_layout.setSpacing(3)

                button = QRadioButton(
                    self.edition_label(
                        variant
                    )
                )

                button.setObjectName(
                    "LibraryEditionChoice"
                )

                button.setProperty(
                    "variantRecord",
                    variant,
                )

                self.button_group.addButton(
                    button
                )

                self._variant_buttons.append(
                    button
                )

                if first_button is None:
                    first_button = button

                if bool(
                    variant.get(
                        "preferred",
                        False,
                    )
                ):
                    preferred_button = (
                        button
                    )

                row_layout.addWidget(
                    button
                )

                detail_text = (
                    self.edition_detail(
                        variant
                    )
                )

                if detail_text:
                    detail = QLabel(
                        detail_text
                    )

                    detail.setObjectName(
                        "LibraryEditionDetail"
                    )

                    detail.setWordWrap(True)

                    row_layout.addWidget(
                        detail
                    )

                group_layout.addWidget(
                    row
                )

            content_layout.addWidget(
                group
            )

        content_layout.addStretch(1)

        scroll.setWidget(content)

        root.addWidget(
            scroll,
            1,
        )

        actions = QHBoxLayout()

        actions.setSpacing(10)

        actions.addStretch(1)

        self.cancel_button = QPushButton(
            "Cancel"
        )

        self.cancel_button.setObjectName(
            "LibraryEditionCancel"
        )

        self.cancel_button.clicked.connect(
            self.reject
        )

        actions.addWidget(
            self.cancel_button
        )

        self.launch_button = QPushButton(
            "▶ Launch Selected Edition"
        )

        self.launch_button.setObjectName(
            "LibraryEditionLaunch"
        )

        self.launch_button.clicked.connect(
            self._accept_selection
        )

        actions.addWidget(
            self.launch_button
        )

        root.addLayout(actions)

        default_button = (
            preferred_button
            or first_button
        )

        if default_button is not None:
            default_button.setChecked(
                True
            )

        self._refresh_launch_state()

        self.button_group.buttonToggled.connect(
            lambda *_args:
            self._refresh_launch_state()
        )

    def _refresh_launch_state(self):
        self.launch_button.setEnabled(
            self.button_group.checkedButton()
            is not None
        )

    def _accept_selection(self):
        button = (
            self.button_group.checkedButton()
        )

        if button is None:
            return

        variant = button.property(
            "variantRecord"
        )

        if not isinstance(
            variant,
            dict,
        ):
            return

        self._selected_variant = (
            variant
        )

        self.accept()

    @classmethod
    def choose(
        cls,
        game,
        parent=None,
    ):
        variants = cls.variants_for_game(
            game
        )

        if len(variants) <= 1:
            return (
                variants[0]
                if variants
                else None
            )

        dialog = cls(
            game,
            parent,
        )

        result = dialog.exec()

        if (
            result
            != QDialog.DialogCode.Accepted
        ):
            return None

        return dialog.selected_variant
