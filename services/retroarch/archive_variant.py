import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArchiveVariant:
    member: str
    title: str
    labels: tuple[str, ...] = ()

    @property
    def display_name(self):
        if not self.labels:
            return self.title

        return (
            f"{self.title} — "
            + " • ".join(self.labels)
        )


class ArchiveVariantFormatter:
    """
    Translate common GoodTools/GoodSet-style filename metadata into
    readable launch-time labels without changing archive identity.

    The original member path is always retained as the authoritative
    value passed to ArchiveRuntime.
    """

    REGION_LABELS = {
        "u": "USA",
        "usa": "USA",
        "e": "Europe",
        "europe": "Europe",
        "j": "Japan",
        "japan": "Japan",
        "w": "World",
        "world": "World",
        "ch": "China",
        "china": "China",
    }

    @classmethod
    def describe(
        cls,
        member,
        preferred=False,
    ):
        filename = Path(member).name
        stem = Path(filename).stem

        labels = []

        if preferred:
            labels.append("Recommended")

        region = cls._region(stem)

        if region:
            labels.append(region)

        if "[!]" in stem:
            labels.append("Verified")

        if re.search(
            r"\[b\d*[^\]]*\]",
            stem,
            re.IGNORECASE,
        ):
            labels.append("Bad Dump")

        if re.search(
            r"\[o\d*[^\]]*\]",
            stem,
            re.IGNORECASE,
        ):
            labels.append("Overdump")

        if re.search(
            r"\[h[^\]]*\]",
            stem,
            re.IGNORECASE,
        ):
            labels.append("Hack")

        if (
            re.search(
                r"\(hack\)",
                stem,
                re.IGNORECASE,
            )
            or " hack)" in stem.casefold()
        ):
            cls._append_unique(
                labels,
                "Hack",
            )

        if re.search(
            r"\[p\d*[^\]]*\]",
            stem,
            re.IGNORECASE,
        ):
            labels.append("Pirate / Unlicensed")

        if re.search(
            r"\(unl\)",
            stem,
            re.IGNORECASE,
        ):
            cls._append_unique(
                labels,
                "Unlicensed",
            )

        translation = re.search(
            r"\[t\+([^\]]+)\]",
            stem,
            re.IGNORECASE,
        )

        if translation:
            labels.append(
                cls._translation_label(
                    translation.group(1)
                )
            )

        trainer = re.search(
            r"\[t(\d+)(?:[^\]]*)\]",
            stem,
            re.IGNORECASE,
        )

        if trainer:
            labels.append(
                f"Trainer {trainer.group(1)}"
            )

        alternate = re.search(
            r"\[a(\d+)(?:[^\]]*)\]",
            stem,
            re.IGNORECASE,
        )

        if alternate:
            labels.append(
                f"Alternate {alternate.group(1)}"
            )

        revision = re.search(
            r"\((?:rev(?:ision)?)[ ._-]*([^)]+)\)",
            stem,
            re.IGNORECASE,
        )

        if revision:
            labels.append(
                f"Revision {revision.group(1).strip()}"
            )

        if re.search(
            r"\((?:proto|prototype)[^)]*\)",
            stem,
            re.IGNORECASE,
        ):
            labels.append("Prototype")

        if re.search(
            r"\(beta[^)]*\)",
            stem,
            re.IGNORECASE,
        ):
            labels.append("Beta")

        if re.search(
            r"\(demo[^)]*\)",
            stem,
            re.IGNORECASE,
        ):
            labels.append("Demo")

        if re.search(
            r"\(sample[^)]*\)",
            stem,
            re.IGNORECASE,
        ):
            labels.append("Sample")

        return ArchiveVariant(
            member=member,
            title=stem,
            labels=tuple(labels),
        )

    @classmethod
    def _region(cls, stem):
        for match in re.finditer(
            r"\(([^()]*)\)",
            stem,
        ):
            token = (
                match.group(1)
                .strip()
                .casefold()
            )

            label = cls.REGION_LABELS.get(
                token
            )

            if label:
                return label

        return ""

    @staticmethod
    def _translation_label(value):
        language = (
            value.split("_", 1)[0]
            .split(",", 1)[0]
            .strip()
        )

        known = {
            "bra": "Brazilian Portuguese",
            "chi": "Chinese",
            "pol": "Polish",
            "rus": "Russian",
            "spa": "Spanish",
            "eng": "English",
            "fre": "French",
            "fra": "French",
            "ger": "German",
            "deu": "German",
            "ita": "Italian",
            "jap": "Japanese",
            "jpn": "Japanese",
            "por": "Portuguese",
        }

        normalized = re.sub(
            r"[^a-z]",
            "",
            language.casefold(),
        )

        for code, label in known.items():
            if normalized.startswith(code):
                return f"Translation: {label}"

        return (
            "Translation"
            if not language
            else f"Translation: {language}"
        )

    @staticmethod
    def _append_unique(
        labels,
        label,
    ):
        if label not in labels:
            labels.append(label)
