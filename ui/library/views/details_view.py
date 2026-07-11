from PyQt6.QtWidgets import (
    QWidget,
    QListWidget,
)



class DetailsView(QWidget):


    def __init__(self, games):

        super().__init__()


        self.list = QListWidget()


        for game in games:


            self.list.addItem(

                f"""
{game.name}

System:
{game.platform}

Year:
{game.year}

Core:
{game.core}
"""

            )


        from PyQt6.QtWidgets import QVBoxLayout


        layout = QVBoxLayout()


        layout.addWidget(
            self.list
        )


        self.setLayout(
            layout
        )
