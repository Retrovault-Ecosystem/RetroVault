from dataclasses import dataclass

from config import ConfigLoader



@dataclass
class LibrarySource:

    id: str

    name: str

    enabled: bool

    type: str

    path: str



class SourceManager:


    def __init__(self, config=None):

        self.config = ConfigLoader().load() if config is None else config



    def sources(self):

        result = []


        for source in self.config.get("library", {}).get("sources", []):


            result.append(

                LibrarySource(

                    id=source["id"],

                    name=source["name"],

                    enabled=source["enabled"],

                    type=source["type"],

                    path=source["path"]

                )

            )


        return result