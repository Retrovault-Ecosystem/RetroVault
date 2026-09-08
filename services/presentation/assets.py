from pathlib import Path
from urllib.parse import urlsplit

from .models import PresentationProfile


class PresentationAssetReferenceResolver:
    """
    Resolve RetroVault portable presentation asset references.

    Portable references use the RetroVault-owned namespace:

        retro-vault://shaders/<relative-path>
        retro-vault://overlays/<relative-path>
        retro-vault://artwork/<relative-path>

    Resolution is rooted in caller-supplied local asset directories.
    Curated recommendation data therefore remains independent of any
    machine-specific absolute filesystem path.

    Values outside the RetroVault namespace are preserved unchanged.
    This keeps existing manual/local presentation assignments compatible.
    """

    SCHEME = "retro-vault"

    def __init__(
        self,
        *,
        shader_root=None,
        overlay_root=None,
        artwork_root=None,
    ):
        self._roots = {
            "shaders": self._normalize_root(shader_root),
            "overlays": self._normalize_root(overlay_root),
            "artwork": self._normalize_root(artwork_root),
        }

    @staticmethod
    def _normalize_root(root):
        if root is None:
            return None

        return Path(root).expanduser().resolve()

    @classmethod
    def is_portable_reference(cls, value):
        return (
            isinstance(value, str)
            and value.startswith(f"{cls.SCHEME}://")
        )

    def resolve_reference(self, value):
        if not isinstance(value, str):
            raise TypeError(
                "Presentation asset reference must be a string."
            )

        if not value:
            return ""

        if not self.is_portable_reference(value):
            return value

        parsed = urlsplit(value)

        if (
            parsed.scheme != self.SCHEME
            or not parsed.netloc
            or not parsed.path
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "Invalid RetroVault presentation asset reference."
            )

        asset_type = parsed.netloc

        if asset_type not in self._roots:
            raise ValueError(
                "Unsupported RetroVault presentation asset type: "
                f"{asset_type}"
            )

        root = self._roots[asset_type]

        if root is None:
            raise ValueError(
                "No local presentation asset root configured for "
                f"{asset_type}."
            )

        relative_text = parsed.path.lstrip("/")

        if not relative_text:
            raise ValueError(
                "RetroVault presentation asset reference "
                "must contain a relative asset path."
            )

        relative = Path(relative_text)

        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(
                "RetroVault presentation asset reference "
                "must remain inside its configured asset root."
            )

        candidate = (root / relative).resolve()

        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError(
                "RetroVault presentation asset reference "
                "escapes its configured asset root."
            ) from exc

        if not candidate.is_file():
            raise ValueError(
                "RetroVault presentation asset does not exist: "
                f"{value}"
            )

        return str(candidate)

    def resolve_profile(
        self,
        profile,
    ) -> PresentationProfile:
        if not isinstance(profile, PresentationProfile):
            raise TypeError(
                "Presentation recommendation must be "
                "a PresentationProfile."
            )

        return PresentationProfile(
            shader=self.resolve_reference(profile.shader),
            overlay=self.resolve_reference(profile.overlay),
            artwork=self.resolve_reference(profile.artwork),
        )
