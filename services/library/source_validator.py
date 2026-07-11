import os


class SourceValidator:


    def validate(self, source):


        problems = []


        path = os.path.expanduser(
            source.path
        )


        if not os.path.exists(path):

            problems.append(
                "Source path does not exist."
            )


        elif not os.path.isdir(path):

            problems.append(
                "Source is not a directory."
            )


        elif not os.access(path, os.R_OK):

            problems.append(
                "Source is not readable."
            )


        return problems
