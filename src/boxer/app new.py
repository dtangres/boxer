import random
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Slot, Qt


class Boxer(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.hello = [
            "Hallo Welt",
            "你好，世界",
            "Hei maailma",
            "Hola Mundo",
            "Привет мир",
        ]

        self.button = QPushButton("Click me!")
        self.text = QLabel("Hello World")
        self.text.setAlignment(Qt.AlignCenter)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

        # Connecting the signal
        self.button.clicked.connect(self.magic)

    @Slot()
    def magic(self):
        self.text.setText(random.choice(self.hello))


def main():
    return Boxer()
