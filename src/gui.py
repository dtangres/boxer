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
    enumToEnglish,
)
from optimization import getOptimumPotionRecipe


class Boxer(toga.App):
    workingIngredientData = {}
    cauldron = None
    potionType = None
    potionTier = None
    starLevel = None

    calculateButton = None

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
            self.adjustColumns()
        except ValueError:
            pass

    async def calculatePotionRecipe(self, widget):
        self.calculateButton.text = "Calculating..."
        self.calculateButton.enabled = False
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
        prettyRecipe = (
            self.prettyPrintPotionRecipe(potionRecipe)
            if potionRecipe
            else "Sorry, no recipe found. Please recheck your inputs and try again."
        )

        # Set up recipe output window
        recipeOutputLabel = toga.Label(
            "Run Boxer to show a recipe here.",
            style=Pack(**self.styleBase),
        )

        recipeOutputBox = toga.Box(
            style=Pack(direction=COLUMN, padding=10),
        )
        recipeOutputBox.add(recipeOutputLabel)
        recipeOutputWindow = toga.Window(
            title="Recipe Output",
        )
        recipeOutputWindow.content = recipeOutputBox

        recipeOutputLabel.text = prettyRecipe
        recipeOutputWindow.show()

        self.calculateButton.enabled = True
        self.calculateButton.text = "Calculate"

    def prettyPrintPotionRecipe(self, potionRecipe):
        ingredientsList = [
            f"- {enumToEnglish[k]}: " + (f"x{v}" * (v > 1))
            for k, v in potionRecipe["ingredients"].items()
        ]
        magiminsList = [
            f"- {k}: {v if v else ''}" for k, v in potionRecipe["magimins"].items()
        ]
        outputStringArray = [
            "Ingredients:",
            "\n".join(ingredientsList),
            "\nMagimins:",
            "\n".join(magiminsList),
            f"\nMinimum Stars: {potionRecipe['baseStars'] + potionRecipe['stabilityStars']}",
            f"Ingredient cost: {potionRecipe['ingredientCosts']}",
        ]
        return "\n".join(outputStringArray)

    def adjustColumns(self):
        self.ingredientsTable._impl.native.get_Columns()[0].set_Width(-1)
        self.ingredientsTable._impl.native.get_Columns()[1].set_Width(-2)

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
        ingredientsTab = toga.Box(style=Pack(flex=1, padding=10))
        self.ingredientsTable = toga.Table(
            headings=[
                "Name",
                "Quantity",
            ],
            data=[
                ("Any", "♾️"),
            ],
            style=Pack(
                **self.styleBase,
                flex=1,
            ),
        )
        ingredientsTab.add(self.ingredientsTable)

        # Set up calculation tab
        calculationTab = toga.Box(
            style=Pack(direction=COLUMN, padding_top=50, padding=10)
        )

        # Tier Select
        print(filterStrings(PotionTier))
        self.tierSelect = toga.Selection(
            items=filterStrings(PotionTier).values(),
            value=list(filterStrings(PotionTier).values())[0],
            style=Pack(**self.styleBase, direction=COLUMN, width=200, padding=5),
        )
        # Star Select
        self.starSlider = toga.Slider(
            min=0,
            max=5,
            value=0,
            tick_count=6,
            style=Pack(direction=COLUMN, width=200, padding=5),
        )

        # Potion Select
        self.potionTypeSelect = toga.Selection(
            items=filterStrings(PotionType).values(),
            value=list(filterStrings(PotionType).values())[0],
            style=Pack(**self.styleBase, direction=COLUMN, width=200, padding=5),
        )

        # Cauldron Select
        self.cauldronSelect = toga.Selection(
            items=filterStrings(Cauldron).values(),
            value=list(filterStrings(Cauldron).values())[0],
            style=Pack(**self.styleBase, direction=COLUMN, width=200, padding=5),
        )

        # Sensory Select
        sensoryBox = toga.Box(
            style=Pack(direction=ROW, padding=5),
        )

        sensorySelectArray = ["Any", "No Bad", "Good"]

        tasteSelectBox = toga.Box(
            style=Pack(direction=COLUMN, padding=5),
        )
        tasteSelectLabel = toga.Label(
            "Taste",
            style=Pack(**self.styleBase, padding=5),
        )
        self.tasteSelectList = toga.Selection(
            items=sensorySelectArray,
            value=sensorySelectArray[0],
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
            items=sensorySelectArray,
            value=sensorySelectArray[0],
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
            items=sensorySelectArray,
            value=sensorySelectArray[0],
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
            items=sensorySelectArray,
            value=sensorySelectArray[0],
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
            items=sensorySelectArray,
            value=sensorySelectArray[0],
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

        # Calculation button
        self.calculateButton = toga.Button(
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
            self.calculateButton,
        )

        container = toga.OptionContainer(
            content=[
                ("Ingredients", ingredientsTab),
                ("Calculation", calculationTab),
            ],
            style=Pack(**self.styleBase),
        )

        # self.commands.add(get_file)
        self.main_window = toga.MainWindow()
        self.main_window.toolbar.add(get_file)
        self.main_window.content = container
        self.adjustColumns()
        self.main_window.show()


def main():
    return Boxer("Boxer", "org.mememagician.boxer")


if __name__ == "__main__":
    main().main_loop()
