import toga
from toga.style.pack import ROW, COLUMN, Pack
from toga.constants import BOLD
from backend import read_reagents
from gameInfo import (
    ingredientData,
    PotionTier,
    PotionType,
    Cauldron,
    filterStrings,
    englishToEnum,
)
from optimization import getOptimumPotionRecipe


def button_handler(widget):
    print("hello")


class Boxer(toga.App):
    workingIngredientData = {}
    cauldron = None
    potionType = None
    potionTier = None
    starLevel = None

    # Establish style base
    fontPath = "../font/static"
    styleBase = {"font_family": "Bitter", "font_size": 14, "font_weight": BOLD}

    # Set up ingredient loading
    async def file_select_handler(self, widget):
        try:
            fname = await self.dialog(toga.OpenFileDialog("Open file with Toga"))
            if fname is not None:
                self.workingIngredientData = read_reagents(fname)
                self.ingredientsTable.data.clear()
                tableRows = [
                    (ingredientData[k]["name"], v)
                    for k, v in self.workingIngredientData.items()
                ][::-1]
                for r in tableRows:
                    self.ingredientsTable.data.insert(0, r)

        except ValueError:
            pass

    async def calculatePotionRecipe(self, widget):
        print(self.workingIngredientData)
        potionRecipe = getOptimumPotionRecipe(
            ingredientInventory=self.workingIngredientData,
            cauldron=self.cauldronSelect.value,
            potionType=self.potionTypeSelect.value,
            tier=self.tierSelect.value,
            starLevel=self.starSlider.value,
            sensoryData={
                "taste": self.tasteSelectList.value,
                "sensation": self.sensationSelectList.value,
                "aroma": self.aromaSelectList.value,
                "visual": self.visualSelectList.value,
                "sound": self.soundSelectList.value,
            },
        )
        print(potionRecipe)

    # Build GUI
    def startup(self):
        # Register font
        toga.Font.register("Bitter", f"{self.fontPath}/Bitter-Regular.ttf")
        toga.Font.register("Bitter", f"{self.fontPath}/Bitter-Bold.ttf", weight=BOLD)

        # Set up commands
        easy_commands = toga.Group("Commands")
        get_file = toga.Command(
            self.file_select_handler,
            text="Load Inventory",
            tooltip="Acquire Inventory from Save File",
            # icon=,
            group=easy_commands,
        )

        # Set up ingredients tab
        ingredientsTab = toga.Box(
            style=Pack(direction=COLUMN, padding_top=50, padding=10)
        )
        self.ingredientsTable = toga.Table(
            headings=[
                "Name",
                "Quantity",
            ],
            style=Pack(**self.styleBase),
        )
        ingredientsTab.add(self.ingredientsTable)

        # Set up calculation tab
        calculationTab = toga.Box(
            style=Pack(direction=COLUMN, padding_top=50, padding=10)
        )
        print(filterStrings(PotionTier))
        self.tierSelect = toga.Selection(
            items=filterStrings(PotionTier).values(),
            value=list(filterStrings(PotionTier).values())[0],
            style=Pack(**self.styleBase, direction=COLUMN, width=200, padding=5),
        )

        self.starSlider = toga.Slider(
            min=0,
            max=5,
            value=0,
            tick_count=6,
            style=Pack(direction=COLUMN, width=200, padding=5),
        )

        self.potionTypeSelect = toga.Selection(
            items=filterStrings(PotionType).values(),
            value=list(filterStrings(PotionType).values())[0],
            style=Pack(**self.styleBase, direction=COLUMN, width=200, padding=5),
        )

        self.cauldronSelect = toga.Selection(
            items=filterStrings(Cauldron).values(),
            value=list(filterStrings(Cauldron).values())[0],
            style=Pack(**self.styleBase, direction=COLUMN, width=200, padding=5),
        )

        sensoryBox = toga.Box(
            style=Pack(direction=ROW, padding=5),
        )

        tasteSelectBox = toga.Box(
            style=Pack(direction=COLUMN, padding=5),
        )
        tasteSelectLabel = toga.Label(
            "Taste",
            style=Pack(**self.styleBase, padding=5),
        )
        self.tasteSelectList = toga.Selection(
            items=["Any", "No Negative", "Positive"],
            value="Any",
            style=Pack(**self.styleBase),
        )
        tasteSelectBox.add(tasteSelectLabel, self.tasteSelectList)

        sensationSelectBox = toga.Box(
            style=Pack(direction=COLUMN, padding=5),
        )
        sensationSelectLabel = toga.Label(
            "Sensation",
            style=Pack(**self.styleBase, padding=5),
        )
        self.sensationSelectList = toga.Selection(
            items=["Any", "No Negative", "Positive"],
            value="Any",
            style=Pack(**self.styleBase),
        )
        sensationSelectBox.add(sensationSelectLabel, self.sensationSelectList)

        aromaSelectBox = toga.Box(
            style=Pack(direction=COLUMN, padding=5),
        )
        aromaSelectLabel = toga.Label(
            "Aroma",
            style=Pack(**self.styleBase, padding=5),
        )
        self.aromaSelectList = toga.Selection(
            items=["Any", "No Negative", "Positive"],
            value="Any",
            style=Pack(**self.styleBase),
        )
        aromaSelectBox.add(aromaSelectLabel, self.aromaSelectList)

        visualSelectBox = toga.Box(
            style=Pack(direction=COLUMN, padding=5),
        )
        visualSelectLabel = toga.Label(
            "Visual",
            style=Pack(**self.styleBase, padding=5),
        )
        self.visualSelectList = toga.Selection(
            items=["Any", "No Negative", "Positive"],
            value="Any",
            style=Pack(**self.styleBase),
        )
        visualSelectBox.add(visualSelectLabel, self.visualSelectList)

        soundSelectBox = toga.Box(
            style=Pack(direction=COLUMN, padding=5),
        )
        soundSelectLabel = toga.Label(
            "Sound",
            style=Pack(**self.styleBase, padding=5),
        )
        self.soundSelectList = toga.Selection(
            items=["Any", "No Negative", "Positive"],
            value="Any",
            style=Pack(**self.styleBase),
        )
        soundSelectBox.add(soundSelectLabel, self.soundSelectList)

        sensoryBox.add(
            tasteSelectBox,
            sensationSelectBox,
            aromaSelectBox,
            visualSelectBox,
            soundSelectBox,
        )

        calculateButton = toga.Button(
            "Calculate",
            on_press=self.calculatePotionRecipe,
            style=Pack(**self.styleBase, direction=ROW, padding=5),
        )

        calculationTab.add(
            self.potionTypeSelect,
            self.tierSelect,
            self.starSlider,
            self.cauldronSelect,
            sensoryBox,
            calculateButton,
        )

        container = toga.OptionContainer(
            content=[
                ("Ingredients", ingredientsTab),
                ("Calculation", calculationTab),
            ],
            style=Pack(**self.styleBase),
        )
        self.commands.add(get_file)
        self.main_window = toga.MainWindow()
        self.main_window.content = container
        self.main_window.show()


def main():
    return Boxer("Boxer", "org.mememagician.boxer")


if __name__ == "__main__":
    main().main_loop()
