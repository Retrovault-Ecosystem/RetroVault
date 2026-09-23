from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(
    frozen=True,
)
class PlatformPresentationPolicy:
    """
    Immutable platform/core policy for RetroVault presentation runtime.

    This policy contains no title/ROM identity and no physical viewport
    coordinates.

    Physical geometry remains owned by the selected RetroVault platform
    presentation package.

    Core options exist only for core-specific source-preservation
    behavior that must be isolated from persistent external RetroArch
    state.
    """

    platform_id: str
    core_identities: tuple[str, ...]
    core_options: Mapping[str, str]

    def __post_init__(
        self,
    ):
        if (
            not isinstance(
                self.platform_id,
                str,
            )
            or not self.platform_id.strip()
        ):
            raise ValueError(
                "Platform ID must be a non-empty string."
            )

        if not isinstance(
            self.core_identities,
            tuple,
        ):
            raise ValueError(
                "Core identities must be a tuple."
            )

        normalized_cores = []

        for identity in self.core_identities:
            if (
                not isinstance(
                    identity,
                    str,
                )
                or not identity.strip()
            ):
                raise ValueError(
                    "Core identities must contain "
                    "non-empty strings."
                )

            normalized = (
                identity
                .strip()
                .lower()
            )

            if normalized in normalized_cores:
                raise ValueError(
                    "Core identities must be unique."
                )

            normalized_cores.append(
                normalized
            )

        if not isinstance(
            self.core_options,
            Mapping,
        ):
            raise ValueError(
                "Core options must be a mapping."
            )

        normalized_options = {}

        for key, value in self.core_options.items():
            if (
                not isinstance(
                    key,
                    str,
                )
                or not key.strip()
            ):
                raise ValueError(
                    "Core option names must be "
                    "non-empty strings."
                )

            if not isinstance(
                value,
                str,
            ):
                raise ValueError(
                    "Core option values must be strings."
                )

            normalized_options[
                key.strip()
            ] = value

        object.__setattr__(
            self,
            "platform_id",
            self.platform_id.strip(),
        )

        object.__setattr__(
            self,
            "core_identities",
            tuple(
                normalized_cores
            ),
        )

        object.__setattr__(
            self,
            "core_options",
            MappingProxyType(
                normalized_options
            ),
        )


class PlatformPresentationPolicyRegistry:
    """
    Resolve canonical RVDB platform identity and RetroArch core identity
    to one explicit RetroVault platform presentation policy.

    Resolution is platform/core based.

    Game titles, ROM filenames, archive names, and game IDs are not part
    of this boundary.
    """

    POLICIES = (
        PlatformPresentationPolicy(
            platform_id="platform.nintendo.nes",
            core_identities=(
                "fceumm",
            ),
            core_options={
                "fceumm_overscan_h_left": "0",
                "fceumm_overscan_h_right": "0",
                "fceumm_overscan_v_top": "0",
                "fceumm_overscan_v_bottom": "0",
            },
        ),
        PlatformPresentationPolicy(
            platform_id="platform.nintendo.snes",
            core_identities=(
                "snes9x",
            ),
            core_options={},
        ),
    )

    @classmethod
    def all(
        cls,
    ):
        return tuple(
            cls.POLICIES
        )

    @classmethod
    def for_platform(
        cls,
        platform_id,
    ):
        if (
            not isinstance(
                platform_id,
                str,
            )
            or not platform_id.strip()
        ):
            return None

        identity = platform_id.strip()

        for policy in cls.POLICIES:
            if policy.platform_id == identity:
                return policy

        return None

    @classmethod
    def for_core(
        cls,
        core_identity,
    ):
        if (
            not isinstance(
                core_identity,
                str,
            )
            or not core_identity.strip()
        ):
            return None

        identity = (
            core_identity
            .strip()
            .lower()
        )

        for policy in cls.POLICIES:
            if identity in policy.core_identities:
                return policy

        return None

    @classmethod
    def resolve(
        cls,
        *,
        platform_id=None,
        core_identity=None,
    ):
        platform_policy = (
            cls.for_platform(
                platform_id
            )
            if platform_id is not None
            else None
        )

        core_policy = (
            cls.for_core(
                core_identity
            )
            if core_identity is not None
            else None
        )

        if (
            platform_policy is not None
            and core_policy is not None
            and platform_policy is not core_policy
        ):
            raise ValueError(
                "Platform/core presentation policy mismatch."
            )

        return (
            platform_policy
            if platform_policy is not None
            else core_policy
        )
