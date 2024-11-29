import toga
from toga.style.pack import ROW, COLUMN, Pack
from toga.constants import BOLD
from boxer.backend import read_reagents
from boxer.gameInfo import (
    ingredientData,
    PotionTier,
    PotionType,
    PotionStability,
    Cauldron,
    filterStrings,
    enumToEnglish,
)
from boxer.optimization import getOptimumPotionRecipe


class Boxer(toga.App):
    workingIngredientData = {}
    cauldron = None
    potionType = None
    potionTier = None
    starLevel = None
    starSliderLabel = None
    currentPotionRecipe = None

    calculateButton = None

    # Establish style base
    fontPath = "resources/font/static"
    styleBase = {"font_family": "Bitter", "font_size": 10, "font_weight": BOLD}

    def brewPotion(self, widget):
        for i, j in self.currentPotionRecipe["ingredients"].items():
            self.workingIngredientData[i] -= j
        self.refreshReagents()
        widget.window.close()

    # Refresh reagents table
    def refreshReagents(self):
        if self.workingIngredientData:
            self.ingredientsTable.data.clear()
            tableRows = [
                (ingredientData[k]["name"], v)
                for k, v in self.workingIngredientData.items()
            ][::-1]
            for r in tableRows:
                self.ingredientsTable.data.insert(0, r)
            self.adjustColumns()

    def starLabelCallback(self, widget):
        self.starSliderLabel.text = f"Stars: {'⭐'*int(widget.value)}"

    def qualityLabelCallback(self, widget):
        self.qualitySliderLabel.text = enumToEnglish[PotionStability(int(widget.value))]

    # Set up ingredient loading
    async def file_select_handler(self, widget):
        try:
            fname = await self.dialog(toga.OpenFileDialog("Open file with Toga"))
            if fname is not None:
                self.workingIngredientData = read_reagents(fname)
                self.refreshReagents()
        except ValueError:
            pass

    async def calculatePotionRecipe(self, widget):
        self.calculateButton.text = "Calculating..."
        self.calculateButton.enabled = False
        # print(self.workingIngredientData)
        self.currentPotionRecipe = getOptimumPotionRecipe(
            ingredientInventory=self.workingIngredientData,
            cauldron=self.cauldronSelect.value,
            potionType=self.potionTypeSelect.value,
            tier=self.tierSelect.value,
            starLevel=self.starSlider.value,
            minStability=PotionStability(self.qualitySlider.value),
            sensoryData={
                "taste": self.tasteSelectList.value,
                "sensation": self.sensationSelectList.value,
                "aroma": self.aromaSelectList.value,
                "visual": self.visualSelectList.value,
                "sound": self.soundSelectList.value,
            },
        )
        prettyRecipe = (
            self.prettyPrintPotionRecipe(self.currentPotionRecipe)
            if self.currentPotionRecipe
            else "Sorry, no recipe found. Please recheck your inputs and try again."
        )

        # Set up recipe output window
        recipeOutputLabel = toga.Label(
            "Run Boxer to show a recipe here.",
            style=Pack(**self.styleBase),
        )

        recipeBrewButton = toga.Button(
            "Brew Recipe",
            on_press=self.brewPotion,
            style=Pack(**self.styleBase),
        )

        recipeOutputBox = toga.Box(
            style=Pack(direction=COLUMN, padding=10),
        )
        recipeOutputBox.add(recipeOutputLabel, recipeBrewButton)
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
            f"- {enumToEnglish[k]}" + (f": x{v}" * (v > 1))
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
            f"Total Magimins: {potionRecipe['totalMagimins']}",
            f"Stability: {potionRecipe['percentStability']}"
            + "%"
            + f" ({potionRecipe['stabilityRank']})",
            f"\nMinimum Quality: {potionRecipe['baseTier'] + ' ' + '⭐'*potionRecipe['normalizedStars']}",
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
        # print(filterStrings(PotionTier))
        self.tierSelect = toga.Selection(
            items=filterStrings(PotionTier).values(),
            value=list(filterStrings(PotionTier).values())[0],
            style=Pack(**self.styleBase, direction=COLUMN, width=200, padding=5),
        )
        # Star Select Box
        starSelectBox = toga.Box(
            style=Pack(direction=ROW, padding=5),
        )
        # Star Select
        self.starSlider = toga.Slider(
            min=0,
            max=5,
            value=0,
            tick_count=6,
            on_change=self.starLabelCallback,
            style=Pack(direction=COLUMN, width=200, padding=5),
        )
        # Star Select Label
        self.starSliderLabel = toga.Label(
            "Stars: -",
            style=Pack(**self.styleBase, padding=5),
        )
        starSelectBox.add(self.starSlider, self.starSliderLabel)

        # Quality Select Box
        qualitySelectBox = toga.Box(
            style=Pack(direction=ROW, padding=5),
        )
        # Quality Select
        self.qualitySlider = toga.Slider(
            min=0,
            max=3,
            value=3,
            tick_count=4,
            on_change=self.qualityLabelCallback,
            style=Pack(direction=COLUMN, width=200, padding=5),
        )
        # Quality Select Label
        self.qualitySliderLabel = toga.Label(
            enumToEnglish[PotionStability.PERFECT],
            style=Pack(**self.styleBase, padding=5),
        )

        qualitySelectBox.add(self.qualitySlider, self.qualitySliderLabel)

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
            starSelectBox,
            qualitySelectBox,
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
        self.icon = toga.Icon("resources/img/ui/coin.ico")
        self.adjustColumns()
        self.main_window.show()


def main():
    return Boxer("Boxer", "org.mememagician.boxer")


if __name__ == "__main__":
    main().main_loop()
