from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from enum import Enum

from services.presentation.master_profile import (
    MasterPresentationClass,
    MasterPresentationProfileRegistry,
)



class PlatformPresentationPolicyState(str, Enum):
    """
    Readiness state for a canonical RVDB platform.

    READY means a validated RetroVault presentation policy exists.

    UNCONFIGURED means the platform is canonical and known, but its
    production presentation policy has not yet been implemented.

    UNCONFIGURED platforms may participate in safe discovery/fallback
    when no core policy is requested, but must never borrow a foreign
    platform policy through core identity.
    """

    READY = "ready"
    UNCONFIGURED = "unconfigured"


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
    master_presentation_class: (
        MasterPresentationClass | None
    ) = None

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

        master_presentation_class = (
            self.master_presentation_class
        )

        if (
            master_presentation_class
            is not None
            and not isinstance(
                master_presentation_class,
                MasterPresentationClass,
            )
        ):
            try:
                master_presentation_class = (
                    MasterPresentationClass(
                        master_presentation_class
                    )
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise ValueError(
                    "Master presentation class must "
                    "be a known reusable profile."
                ) from exc

        if master_presentation_class is not None:
            (
                MasterPresentationProfileRegistry
                .require(
                    master_presentation_class
                )
            )

        object.__setattr__(
            self,
            "master_presentation_class",
            master_presentation_class,
        )


# Canonical platform/core compatibility authority.
#
# This map describes platform/core compatibility independently from
# presentation readiness. A platform may have a known launch core
# while still being UNCONFIGURED for RetroVault production visuals.
#
# Values use normalized Libretro core identities, not filesystem
# filenames. Library compatibility adapters may translate these
# identities to historical *_libretro.so values.
#
# Only compatibility already established by the current production
# Library is declared here. Unsupported/unknown canonical platforms
# remain explicit canonical identities without an invented core.
PLATFORM_CORE_COMPATIBILITY = {
    "platform.arcade": (
        "mame",
    ),
    "platform.nintendo.n64": (
        "mupen64plus_next",
    ),
    "platform.nintendo.nes": (
        "fceumm",
    ),
    "platform.nintendo.snes": (
        "snes9x",
    ),
    "platform.sega.genesis": (
        "genesis_plus_gx",
    ),
    "platform.sega.game.gear": (
        "genesis_plus_gx",
    ),
    "platform.sega.master.system": (
        "genesis_plus_gx",
    ),
    "platform.sega.sg1000": (
        "genesis_plus_gx",
    ),
}


class PlatformPresentationPolicyRegistry:
    PLATFORM_CORE_COMPATIBILITY = PLATFORM_CORE_COMPATIBILITY
    # Explicit readiness state for every canonical RVDB platform.
    # Physical viewport geometry remains package-owned.
    PLATFORM_STATES = {
        "platform.arcade": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.atari.2600": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.atari.5200": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.atari.7800": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.atari.8.bit.computers": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.atari.jaguar": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.atari.lynx": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.atari.st": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.nintendo.3ds": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.nintendo.ds": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.nintendo.game.boy": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.nintendo.game.boy.advance": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.nintendo.game.boy.color": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.nintendo.gamecube": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.nintendo.n64": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.nintendo.nes": PlatformPresentationPolicyState.READY,
        "platform.nintendo.snes": PlatformPresentationPolicyState.READY,
        "platform.nintendo.wii": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.nintendo.wii.u": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.sega.dreamcast": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.sega.game.gear": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.sega.genesis": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.sega.master.system": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.sega.saturn": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.sega.sc3000": PlatformPresentationPolicyState.UNCONFIGURED,
        "platform.sega.sg1000": PlatformPresentationPolicyState.UNCONFIGURED,
    }

    @classmethod
    def state_for(cls, platform_id):
        if not isinstance(platform_id, str):
            return None

        platform_id = platform_id.strip()

        if not platform_id:
            return None

        return cls.PLATFORM_STATES.get(platform_id)

    @classmethod
    def canonical_platform_ids(cls):
        return tuple(cls.PLATFORM_STATES)

    @classmethod
    def ready_platform_ids(cls):
        return tuple(
            platform_id
            for platform_id, state
            in cls.PLATFORM_STATES.items()
            if state
            is PlatformPresentationPolicyState.READY
        )

    @classmethod
    def unconfigured_platform_ids(cls):
        return tuple(
            platform_id
            for platform_id, state
            in cls.PLATFORM_STATES.items()
            if state
            is PlatformPresentationPolicyState.UNCONFIGURED
        )

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
                PLATFORM_CORE_COMPATIBILITY[
                    "platform.nintendo.nes"
                ]
            ),
            core_options={
                "fceumm_overscan_h_left": "0",
                "fceumm_overscan_h_right": "0",
                "fceumm_overscan_v_top": "0",
                "fceumm_overscan_v_bottom": "0",
            },
            master_presentation_class=(
                MasterPresentationClass.CLASSIC_4_3
            ),
        ),
        PlatformPresentationPolicy(
            platform_id="platform.nintendo.snes",
            core_identities=(
                PLATFORM_CORE_COMPATIBILITY[
                    "platform.nintendo.snes"
                ]
            ),
            core_options={},
            master_presentation_class=(
                MasterPresentationClass.CLASSIC_4_3
            ),
        ),
    )

    @classmethod
    def master_presentation_class_for(
        cls,
        platform_id,
    ):
        """
        Return the reusable Master Presentation class explicitly
        assigned to one production-ready platform policy.

        Presentation class assignment is intentionally distinct from
        physical production geometry. Existing platform packages remain
        authoritative for deployed viewport coordinates until a later
        qualified migration boundary.

        UNCONFIGURED, unknown, handheld, dual-screen, and other
        not-yet-qualified platforms return None rather than borrowing
        an inappropriate presentation class.
        """
        policy = cls.for_platform(
            platform_id
        )

        if policy is None:
            return None

        return policy.master_presentation_class

    @classmethod
    def master_presentation_profile_for(
        cls,
        platform_id,
    ):
        """
        Resolve one platform's reusable Master Presentation profile.

        Returns None when no explicit reusable presentation class has
        been qualified for the platform.
        """
        profile_class = (
            cls.master_presentation_class_for(
                platform_id
            )
        )

        if profile_class is None:
            return None

        return (
            MasterPresentationProfileRegistry
            .require(
                profile_class
            )
        )

    @classmethod
    def compatible_core_identities(
        cls,
        platform_id,
    ):
        """
        Return canonical normalized core identities known to be
        compatible with one canonical RVDB platform.

        Presentation readiness is intentionally independent. An
        UNCONFIGURED platform may still have a known launch core.
        """

        if not isinstance(
            platform_id,
            str,
        ):
            return ()

        platform_id = platform_id.strip()

        if (
            platform_id
            not in cls.PLATFORM_STATES
        ):
            return ()

        return tuple(
            PLATFORM_CORE_COMPATIBILITY.get(
                platform_id,
                (),
            )
        )

    @classmethod
    def is_core_compatible(
        cls,
        platform_id,
        core_identity,
    ):
        """
        Return True only when an explicit canonical platform/core
        pair is known compatible.

        Unknown platforms, unknown cores, and non-string identities
        never become implicit compatibility policy.
        """

        if not isinstance(
            core_identity,
            str,
        ):
            return False

        core_identity = (
            core_identity
            .strip()
            .casefold()
        )

        if not core_identity:
            return False

        # Accept the Library's historical Libretro filename form,
        # absolute core paths, and normalized policy identities.
        core_name = (
            core_identity
            .replace("\\", "/")
            .rsplit("/", 1)[-1]
        )

        if core_name.endswith(
            "_libretro.so"
        ):
            core_name = core_name[
                :-len("_libretro.so")
            ]
        elif core_name.endswith(
            ".so"
        ):
            core_name = core_name[
                :-len(".so")
            ]

        return core_name in (
            cls.compatible_core_identities(
                platform_id
            )
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
        # Canonical platform identity is meaningful only when supplied
        # as a non-empty string. This preserves legacy callers and test
        # doubles whose platform_id attribute may be absent or non-string.
        explicit_platform_id = (
            platform_id.strip()
            if isinstance(platform_id, str)
            else None
        )

        if not explicit_platform_id:
            explicit_platform_id = None

        explicit_core_identity = (
            core_identity.strip()
            if isinstance(core_identity, str)
            else None
        )

        if not explicit_core_identity:
            explicit_core_identity = None

        if explicit_platform_id is None:
            return (
                cls.for_core(
                    explicit_core_identity
                )
                if explicit_core_identity is not None
                else None
            )

        state = cls.state_for(
            explicit_platform_id
        )

        platform_policy = cls.for_platform(
            explicit_platform_id
        )

        # Safe discovery/fallback remains valid when no core policy is
        # requested. A known UNCONFIGURED or unknown platform therefore
        # resolves to no policy rather than raising.
        if explicit_core_identity is None:
            return platform_policy

        core_policy = cls.for_core(
            explicit_core_identity
        )

        # Once both an explicit platform and a recognized core policy
        # exist, they must identify the same platform. This closes the
        # cross-platform borrowing defect.
        if core_policy is not None:
            if platform_policy is None:
                raise ValueError(
                    "Explicit platform cannot borrow a foreign "
                    "core presentation policy."
                )

            if platform_policy is not core_policy:
                raise ValueError(
                    "Platform/core presentation policy mismatch."
                )

            return platform_policy

        # A READY platform paired with an unknown/unregistered core
        # cannot be proven compatible.
        if (
            state
            is PlatformPresentationPolicyState.READY
        ):
            raise ValueError(
                "Core identity does not match READY platform "
                "presentation policy."
            )

        # UNCONFIGURED/unknown platform + unknown core has no policy
        # available to borrow. Returning None is safe and preserves
        # existing fallback semantics.
        return None
