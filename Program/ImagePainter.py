import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QAction, QFileDialog
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QRectF

class ImageDrawer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create the QGraphicsView and QGraphicsScene
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)

        # Store the drawn rectangles
        self.rectangles = []

        # Set up the pen for drawing rectangles
        self.pen = QPen(Qt.red)
        self.pen.setWidth(2)

        # Create the menu actions
        open_action = QAction("Open Image", self)
        open_action.triggered.connect(self.open_image)

        # Create the menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(open_action)

        # Connect the mouse events
        self.view.mousePressEvent = self.mouse_press_event
        self.view.mouseReleaseEvent = self.mouse_release_event

    def open_image(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)", options=options)
        if file_path:
            # Load the selected image
            self.image = QPixmap(file_path)
            self.scene.clear()
            self.scene.addPixmap(self.image)

    def mouse_press_event(self, event):
        if event.button() == Qt.LeftButton and self.image:
            self.start_point = event.pos()

    def mouse_release_event(self, event):
        if event.button() == Qt.LeftButton and self.image:
            end_point = event.pos()
            rect = self.create_rectangle(self.start_point, end_point)
            self.rectangles.append(rect)
            self.scene.addItem(rect)

    def create_rectangle(self, start_point, end_point):
        rect = QGraphicsRectItem()
        rect.setPen(self.pen)
        rect.setRect(QRectF(start_point, end_point))
        return rect


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageDrawer()
    window.show()
    sys.exit(app.exec_())
