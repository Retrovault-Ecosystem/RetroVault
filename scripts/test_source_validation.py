from services.library import (
    SourceManager,
    SourceValidator,
)


manager = SourceManager()

validator = SourceValidator()


for source in manager.sources():

    print()
    print(source.name)


    result = validator.validate(
        source
    )


    if result:

        print("Problems:")

        for item in result:

            print("-", item)

    else:

        print("READY")
