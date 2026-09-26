_LIBRETRO_SUFFIXES = (
    "_libretro.so",
    "_libretro.dll",
    "_libretro.dylib",
    "_libretro",
)


def canonical_libretro_core_identity(
    core,
):
    """
    Return the canonical semantic identity of one Libretro core.

    The input may be a canonical identity, a Libretro filename, or an
    absolute/relative filesystem path expressed with POSIX or Windows
    path separators.

    Runtime launch code keeps the original filesystem path for
    RetroArch's -L argument. Semantic policy authorities consume only
    this normalized identity.

    This function deliberately contains no platform, game, ROM, raster,
    presentation, or geometry knowledge.
    """

    if not isinstance(
        core,
        str,
    ):
        raise ValueError(
            "Core identity must be a string."
        )

    value = core.strip()

    if not value:
        raise ValueError(
            "Core identity cannot be empty."
        )

    # Core identity is a representation boundary rather than a host-OS
    # filesystem operation. Accept both Libretro path conventions
    # regardless of the OS on which RetroVault itself is running.
    name = (
        value
        .replace("\\", "/")
        .rsplit("/", 1)[-1]
        .casefold()
    )

    for suffix in _LIBRETRO_SUFFIXES:
        if name.endswith(suffix):
            name = name[
                :-len(suffix)
            ]
            break

    if name.startswith("lr-"):
        name = name[3:]

    if not name:
        raise ValueError(
            "Core identity cannot be empty."
        )

    return name
