import sys
from PySide6.QtWidgets import QApplication
from boxer.app import Boxer

if __name__ == "__main__":
    app = QApplication(sys.argv)

    widget = Boxer()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
