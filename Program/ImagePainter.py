import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QAction, QFileDialog
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QBrush, QPalette, QCursor
from PyQt5.QtCore import Qt, QRectF, QTimer, QPoint

class ImageDrawer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create the QGraphicsView and QGraphicsScene
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)

        # Store the drawn rectangles
        self.annotations = []
        self.currentAnnotation = None

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

        # Timers
        self.timer = QTimer()
        self.timer.timeout.connect(self.drawing_annotation)

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
            start_point = event.pos()
            self.currentAnnotation = Annotation(start_point)
            self.drawing_annotation()
            self.timer.start(16)


        if event.button() == Qt.RightButton and self.image:
            anno = self.annotations.pop()
            self.scene.removeItem(anno.rect)
            self.scene.removeItem(anno.text)

            #for rectangle in self.annotations:
            #    self.scene.removeItem(rectangle.rect)
            #    self.scene.removeItem(rectangle.text)

    def mouse_release_event(self, event):
        if event.button() == Qt.LeftButton and self.image:
            self.timer.stop()

            end_point = self.centralWidget().mapFromGlobal(QCursor.pos())
            self.currentAnnotation.finalize(end_point)

            self.annotations.append(self.currentAnnotation)
            self.scene.addItem(self.currentAnnotation.rect)
            self.scene.addItem(self.currentAnnotation.text)

    def drawing_annotation(self):
        end_point = self.centralWidget().mapFromGlobal(QCursor.pos())
        self.currentAnnotation.draw(end_point)
        self.scene.addItem(self.currentAnnotation.rect)

class Annotation():
    def __init__(self, start_point):
        self.rect = QGraphicsRectItem()
        self.start_point = start_point
        self.end_point = None

        self.pen = QPen(Qt.red)
        self.pen.setWidth(2)
        self.rect.setPen(self.pen)

        self.scene = QGraphicsScene()
        self.scene.addText("")
        self.text = self.scene.items()[0]

    def draw(self, end_point):
        self.end_point = end_point
        start = QPoint(self.start_point.x(), self.start_point.y())

        if (self.start_point.x() > self.end_point.x()):
            start.setX(self.end_point.x())
            end_point.setX(self.start_point.x())

        if (self.start_point.y() > self.end_point.y()):
            start.setY(self.end_point.y())
            end_point.setY(self.start_point.y())

        self.rect.setRect(QRectF(start, end_point))

    def finalize(self, end_point):
        self.end_point = end_point
        start = QPoint(self.start_point.x(), self.start_point.y())

        if (self.start_point.x() > self.end_point.x()):
            start.setX(self.end_point.x())
            end_point.setX(self.start_point.x())

        if (self.start_point.y() > self.end_point.y()):
            start.setY(self.end_point.y())
            end_point.setY(self.start_point.y())

        self.rect.setRect(QRectF(start, end_point))
        self.text.setPos(start.x() - 5, start.y() - 16)
        self.text.setHtml("<div style='color: white; background-color: red;'>Label</div>")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageDrawer()
    window.show()
    sys.exit(app.exec_())
