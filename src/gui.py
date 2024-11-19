import toga
from backend import read_reagents
from gameInfo import ingredientData


def button_handler(widget):
    print("hello")


class Boxer(toga.App):
    workingIngredientData = {}

    async def file_select_handler(self, widget):
        try:
            fname = await self.dialog(toga.OpenFileDialog("Open file with Toga"))
            if fname is not None:
                workingIngredientData = read_reagents(fname)
                self.ingredientsTable.data.clear()
                tableRows = [
                    (ingredientData[k]["name"], v)
                    for k, v in workingIngredientData.items()
                ][::-1]
                for r in tableRows:
                    self.ingredientsTable.data.insert(0, r)

        except ValueError:
            pass

    def startup(self):
        box = toga.Box()

        easy_commands = toga.Group("Commands")
        get_file = toga.Command(
            self.file_select_handler,
            text="Load Inventory",
            tooltip="Acquire Inventory from Save File",
            # icon=,
            group=easy_commands,
        )

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

        self.commands.add(get_file)
        split.content = [self.ingredientsTable, potionsPanel]
        self.main_window = toga.MainWindow()
        self.main_window.content = split
        self.main_window.show()


def main():
    return Boxer("Boxer", "org.mememagician.boxer")


if __name__ == "__main__":
    main().main_loop()
