import sys
from image_drawer import ImageDrawer
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageDrawer()
    window.show()
    sys.exit(app.exec_())
