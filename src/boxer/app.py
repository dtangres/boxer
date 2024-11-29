from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget, QFileDialog
from PySide6.QtCore import Slot, Qt

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


class Boxer(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.workingIngredientData = {}
        self.cauldron = None
        self.potionType = None
        self.potionTier = None
        self.starLevel = None
        self.starSliderLabel = None
        self.currentPotionRecipe = None
        self.calculateButton = None

        # TODO Add font stuff

        self.loadInvButton = QPushButton("Load Inventory")
        self.loadInvButton.clicked.connect(self.fileSelectHandler)

        # self.hello = [
        #     "Hallo Welt",
        #     "你好，世界",
        #     "Hei maailma",
        #     "Hola Mundo",
        #     "Привет мир",
        # ]

        # self.button = QPushButton("Click me!")
        # self.text = QLabel("Hello World")
        # self.text.setAlignment(Qt.AlignCenter)

        # self.layout = QVBoxLayout()
        # self.layout.addWidget(self.text)
        self.layout.addWidget(self.loadInvButton)
        self.setLayout(self.layout)

        # Connecting the signal
        # self.button.clicked.connect(self.magic)

    # Set up ingredient loading
    def fileSelectHandler(self, widget):
        try:
            fname, check = QFileDialog.getOpenFileName(
                self,
                caption=self.tr("Open Image"),
            )
            if check:
                print("Scrinted Biste")
                # TODO Implement this
                # self.workingIngredientData = read_reagents(fname)
                # self.refreshReagents()
        except ValueError:
            pass

    # @Slot()
    # def magic(self):
    #     self.text.setText("e")


def main():
    return Boxer()
