from services.library import (
    SourceManager,
    RomScanner,
)



manager = SourceManager()

scanner = RomScanner()



for source in manager.sources():


    games = scanner.scan(source)


    print()

    print(
        source.name
    )


    print(
        "Games found:",
        len(games)
    )


    for game in games[:10]:

        print(
            game.name,
            "-",
            game.platform
        )
