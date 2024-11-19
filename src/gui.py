import toga
from backend import read_reagents
from gameInfo import ingredientData


def button_handler(widget):
    print("hello")


class Boxer(toga.App):

    def startup(self):
        box = toga.Box()


        split = toga.SplitContainer()

        ingredientsPanel = toga.Box()
        self.ingredientsTable = toga.Table(
            headings=[
                "Name",
                "Quantity",
            ]
        )

        box.add(ingredientsPanel)

        potionsPanel = toga.Box()
        box.add(potionsPanel)

        split.content = [self.ingredientsTable, potionsPanel]
        self.main_window = toga.MainWindow()
        self.main_window.content = split
        self.main_window.show()


def main():
    return Boxer("Boxer", "org.mememagician.boxer")


if __name__ == "__main__":
    main().main_loop()
