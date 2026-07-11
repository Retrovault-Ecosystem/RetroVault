class LaunchDiagnostics:



    def explain(
        self,
        report
    ):


        messages = []



        if not report["retroarch"]:

            messages.append(

                "RetroArch was not found."

            )



        if not report["core"]:

            messages.append(

                "Required core is missing."

            )



        if not report["rom"]:

            messages.append(

                "ROM file does not exist."

            )



        if not messages:

            messages.append(

                "Game is ready to launch."

            )


        return messages
