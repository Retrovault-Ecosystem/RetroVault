from services.presentation.platform_policy import (
    PlatformPresentationPolicyRegistry,
)


# Historical Library display-name compatibility.
#
# Public CoreMapper.get_core(platform) behavior is preserved. The
# values are now canonical RVDB platform identities rather than an
# independent platform->core policy table.
PLATFORM_ALIASES = {
    "Nintendo Entertainment System":
        "platform.nintendo.nes",

    "NES":
        "platform.nintendo.nes",

    "Super Nintendo":
        "platform.nintendo.snes",

    "Super Nintendo Entertainment System":
        "platform.nintendo.snes",

    "SNES":
        "platform.nintendo.snes",

    "Sega Genesis":
        "platform.sega.genesis",

    "Genesis":
        "platform.sega.genesis",

    "Nintendo 64":
        "platform.nintendo.n64",

    "Arcade":
        "platform.arcade",
}


def _libretro_filename(
    core_identity,
):
    core_identity = str(
        core_identity
        or ""
    ).strip()

    if not core_identity:
        return ""

    return (
        f"{core_identity}_libretro.so"
    )


# Compatibility export retained for existing consumers/tests that
# import CORE_MAP directly. It is derived from canonical authority;
# it is no longer an independent source of platform/core truth.
CORE_MAP = {
    platform_name: _libretro_filename(
        (
            PlatformPresentationPolicyRegistry
            .compatible_core_identities(
                platform_id
            )
            or ("",)
        )[0]
    )
    for platform_name, platform_id
    in PLATFORM_ALIASES.items()
}


class CoreMapper:

    def get_core(
        self,
        platform,
    ):
        platform_id = (
            PLATFORM_ALIASES.get(
                platform,
                "",
            )
        )

        if not platform_id:
            return ""

        cores = (
            PlatformPresentationPolicyRegistry
            .compatible_core_identities(
                platform_id
            )
        )

        # CoreMapper historically selected exactly one core. Preserve
        # that behavior only when canonical authority has exactly one
        # compatible core. Multiple-core policy must be chosen at a
        # higher explicit policy boundary rather than silently here.
        if len(cores) != 1:
            return ""

        return _libretro_filename(
            cores[0]
        )
