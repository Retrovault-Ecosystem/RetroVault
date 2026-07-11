from services.library import (
    SourceManager,
    LibraryBuilder,
)


sources = SourceManager()


builder = LibraryBuilder()


games = builder.build(
    sources.sources()
)


print()

print(
    "Total games:",
    len(games)
)


for game in games[:10]:

    print()

    print(
        game.name
    )

    print(
        "Platform:",
        game.platform
    )

    print(
        "Core:",
        game.core
    )

    print(
        "ROM:",
        game.rom
    )
