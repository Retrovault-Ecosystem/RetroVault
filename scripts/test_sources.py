from services.library import SourceManager



manager = SourceManager()



for source in manager.sources():

    print("----------------")

    print("ID:", source.id)

    print("Name:", source.name)

    print("Enabled:", source.enabled)

    print("Type:", source.type)

    print("Path:", source.path)