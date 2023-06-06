import sys, threading, math, os, cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QAction, \
    QFileDialog, QPushButton, QWidget, QLabel, QLineEdit, QTextEdit
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QBrush, QPalette, QCursor, QIcon
from PyQt5.QtCore import Qt, QRectF, QTimer, QPoint, QRect

global window

class ImageDrawer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create the QGraphicsView and QGraphicsScene
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)
        self.image = None
        self.line_label = None
        self.action = 0 # 0 select   1 create   2 edit   3 delete

        # Set window properties
        self.setWindowState(Qt.WindowMaximized)
        self.setWindowTitle("Full Screen Example")

        # Store pre-existing annotations
        self.preExistingAnnotations = []

        # Store the drawn rectangles
        self.annotations = []
        self.currentAnnotation = None
        self.possibleSelectAnnotations = []
        self.selectedAnnotationIndex = 0

        # Create the menu actions
        open_action = QAction("Open Image", self)
        open_action.triggered.connect(self.open_image)
        open_action2 = QAction("Open Folder", self)
        open_action2.triggered.connect(self.open_folder)

        # Create the menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(open_action)
        file_menu.addAction(open_action2)

        # Connect the mouse events
        self.scene.mousePressEvent = self.mouse_press_event
        self.scene.mouseReleaseEvent = self.mouse_release_event
        self.scene.keyPressEvent = self.key_press_event

        # Timers
        self.timer = QTimer()
        self.timer.timeout.connect(self.drawing_annotation)


        # Create the buttons
        button1 = QPushButton("Select", self)
        button1.setIcon(QIcon('cursor.png'))
        button1.clicked.connect(self.action_select)

        button2 = QPushButton("Create", self)
        button2.setIcon(QIcon('box.png'))
        button2.clicked.connect(self.action_create)

        button3 = QPushButton("Label", self)
        button3.setIcon(QIcon('font.png'))
        button3.clicked.connect(self.action_label)

        button4 = QPushButton("Delete", self)
        button4.setIcon(QIcon('delete.png'))
        button4.clicked.connect(self.action_delete)

        # Add the buttons to the toolbar
        toolbar = self.addToolBar("Buttons")
        toolbar.addWidget(button1)
        toolbar.addWidget(button2)
        toolbar.addWidget(button3)
        toolbar.addWidget(button4)

        # Create an empty label for the image
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setStyleSheet("background-color: white; border: none;")


    def open_image(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)", options=options)
        if file_path:
            # Load the selected image
            self.image = QPixmap(file_path)
            self.scene.clear()
            self.scene.addPixmap(self.image)

    def open_folder(self):
        default_dir = '/path/to/default/directory'
        options = QFileDialog.Options()
        #options |= QFileDialog.Directory
        selected_dir = QFileDialog.getExistingDirectory(window, "Select Directory", default_dir, options=options)

        if selected_dir:
            selected_folder = selected_dir
            images_dir = os.path.join(selected_folder)
            image_files = sorted(os.listdir(images_dir))
            labels_dir = os.path.join(selected_folder, 'labels')
            labels_files = sorted(os.listdir(labels_dir))
            first_image_path = os.path.join(images_dir, image_files[1])
            first_label_path = os.path.join(labels_dir, labels_files[0])
            image_dir = first_image_path
            label_dir = first_label_path
            self.image = QPixmap(first_image_path)
            self.scene.clear()
            self.scene.addPixmap(self.image)
            self.read_labels(images_dir, image_dir, label_dir)

    def mouse_press_event(self, event):
        if event.button() == Qt.LeftButton and self.image and event.type() == event.GraphicsSceneMousePress:
            if (self.action == 0):
                mouse_pos = event.scenePos()

                self.currentAnnotation = None
                annotations = []
                for annotation in self.annotations:
                    annotation.deselect()
                    if (annotation.start_point.x() < mouse_pos.x() < annotation.end_point.x() and
                            annotation.start_point.y() < mouse_pos.y() < annotation.end_point.y()):
                        annotations.append(annotation)

                if (annotations != []):
                    if (annotations == self.possibleSelectAnnotations):
                        self.selectedAnnotationIndex += 1
                    else:
                        self.selectedAnnotationIndex = 0

                    self.possibleSelectAnnotations = annotations
                    self.currentAnnotation = self.possibleSelectAnnotations[self.selectedAnnotationIndex % len(self.possibleSelectAnnotations)]
                    self.currentAnnotation.select()

            if (self.action == 1):
                start_point = event.scenePos()
                start_point.setX(round(start_point.x()))
                start_point.setY(round(start_point.y()))

                self.currentAnnotation = Annotation(start_point)
                self.drawing_annotation()
                self.timer.start(16)

    def mouse_release_event(self, event):
        if event.button() == Qt.LeftButton and self.image:
            if (self.action == 1):
                self.timer.stop()

                end_point = self.centralWidget().mapFromGlobal(QCursor.pos())
                end_point.setX(round(end_point.x() - (self.centralWidget().width() - self.image.width()) / 2))
                end_point.setY(round(end_point.y() - (self.centralWidget().height() - self.image.height()) / 2))
                self.currentAnnotation.finalize()

                self.annotations.append(self.currentAnnotation)
                self.scene.addItem(self.currentAnnotation.rect)
                self.scene.addItem(self.currentAnnotation.text)

    def key_press_event(self, event):
        if (event.key() == Qt.Key_S):
            self.action = 0
        if (event.key() == Qt.Key_C):
            self.action = 1
        if (event.key() == Qt.Key_E):
            self.action = 2
            if (self.currentAnnotation != None and self.line_label == None):
                self.line_label = QLineEdit(self)
                self.line_label.move(int(self.width() / 2), int(self.height() / 2))
                self.line_label.resize(80, 20)
                self.line_label.setPlaceholderText(self.currentAnnotation.label)
                self.line_label.editingFinished.connect(self.close_line_label)
                self.line_label.show()
        if (event.key() == Qt.Key_D):
            self.action = 3
            if (self.currentAnnotation != None):
                anno = self.annotations.pop(self.annotations.index(self.currentAnnotation))
                self.scene.removeItem(anno.rect)
                self.scene.removeItem(anno.text)
                self.currentAnnotation = None

    def action_select(self):
        self.action = 0

    def action_create(self):
        self.action = 1

    def action_label(self):
        self.action = 2
        if (self.currentAnnotation != None and self.line_label == None):
            self.line_label = QLineEdit(self)
            self.line_label.move(int(self.width() / 2), int(self.height() / 2))
            self.line_label.resize(80, 20)
            self.line_label.setPlaceholderText(self.currentAnnotation.label)
            self.line_label.editingFinished.connect(self.close_line_label)
            self.line_label.show()

    def action_delete(self):
        self.action = 3
        if (self.currentAnnotation != None):
            anno = self.annotations.pop(self.annotations.index(self.currentAnnotation))
            self.scene.removeItem(anno.rect)
            self.scene.removeItem(anno.text)
            self.currentAnnotation = None

    def close_line_label(self):
        if (self.line_label != None and self.currentAnnotation != None):
            self.currentAnnotation.label = self.line_label.text()
            self.currentAnnotation.deselect()
            self.line_label.close()
            self.line_label = None
            self.currentAnnotation = None

    def drawing_annotation(self):
        self.currentAnnotation.draw()
        self.scene.addItem(self.currentAnnotation.rect)

    # Reads the COCO text file and put it into coordinates
    def read_labels(self, images_dir, image_dir, label_dir):
        # Iterate over the images in the directory
        for image_file in os.listdir(images_dir):
            if image_file.endswith('.jpg') or image_file.endswith('.png') or image_file.endswith('.jpeg'):

                # Clear the list if another image is opened
                if len(self.preExistingAnnotations) > 0:
                    self.preExistingAnnotations.clear()

                # Load the image
                image = cv2.imread(image_dir)

                # Read the labels from the file
                with open(label_dir, 'r') as f:
                    lines = f.readlines()

                # Process each line in the label file
                for line in lines:
                    line = line.strip().split()
                    class_id = int(line[0])
                    x, y, w, h = map(float, line[1:5])
                    class_name = 'test'  # names[class_id]  # assuming you have loaded the class names
                    color = 1  # colors[class_id]  # assuming you have loaded the colors
                    self.preExistingAnnotations.append([class_id, class_name, color, x, y, w, h])
        for annotation in self.preExistingAnnotations:
            img_h, img_w, _ = image.shape
            x1 = int((annotation[3] - annotation[5] / 2) * img_w)
            y1 = int((annotation[4] - annotation[6] / 2) * img_h)
            x2 = int((annotation[3] + annotation[5] / 2) * img_w)
            y2 = int((annotation[4] + annotation[6] / 2) * img_h)

            # Draw the bounding box on the image
            self.currentAnnotation = Annotation(QPoint(x1, y1), QPoint(x2, y2))

            self.annotations.append(self.currentAnnotation)
            self.scene.addItem(self.currentAnnotation.rect)
            self.scene.addItem(self.currentAnnotation.text)

    # def write_labels(self, List):
    #     if len(self.preExistingAnnotations) > 0:
    #         for annotation in List:
    #         # [0, 'test', 1, 0.84, 0.577667, 0.0906667, 0.146]
    #             self.rect.setRect(QRectF(annotation[3], annotation[5]))
    #             self.text.setPos(annotation[3].x() - 5, annotation[4].y() - 16)
    #             self.text.setHtml("<div style='color: white; background-color: red;'>Label</div>")
    #     else:
    #         print("List was empty")


class Annotation():
    def __init__(self, start_point, end_point=None, label="Label"):
        self.rect = QGraphicsRectItem()
        self.start_point = start_point
        self.end_point = None
        self.width = None
        self.height = None
        self.label = label
        self.start_point_mouse = QCursor.pos()

        self.pen = QPen(Qt.red)
        self.pen.setWidth(2)
        self.rect.setPen(self.pen)

        self.scene = QGraphicsScene()
        self.scene.addText("")
        self.text = self.scene.items()[0]

        if (end_point != None):
            self.rect.setRect(QRectF(start_point, end_point))
            self.text.setPos(start_point.x() - 5, start_point.y() - 16)
            self.text.setHtml(f"<div style='color: white; background-color: red;'>{self.label}</div>")

    def select(self):
        self.pen.setColor(Qt.green)
        self.rect.setPen(self.pen)
        self.rect.setRect(QRectF(self.start_point, self.end_point))
        self.text.setHtml(f"<div style='color: white; background-color: green;'>{self.label}</div>")

    def deselect(self):
        self.pen.setColor(Qt.red)
        self.rect.setPen(self.pen)
        self.rect.setRect(QRectF(self.start_point, self.end_point))
        self.text.setHtml(f"<div style='color: white; background-color: red;'>{self.label}</div>")

    def draw(self):
        end_point_mouse = QCursor.pos()
        total_mouse = end_point_mouse - self.start_point_mouse
        self.width = total_mouse.x()
        self.height = total_mouse.y()
        self.end_point = QPoint(int(self.start_point.x() + self.width), int(self.start_point.y() + self.height))
        start = QPoint(int(self.start_point.x()), int(self.start_point.y()))
        end = QPoint(int(self.end_point.x()), int(self.end_point.y()))

        if (self.width < 0):
            start.setX(self.end_point.x())
            end.setX(int(self.start_point.x()))

        if (self.height < 0):
            start.setY(self.end_point.y())
            end.setY(int(self.start_point.y()))

        start.setX( max(0, start.x()) )
        start.setY( max(0, start.y()) )
        end.setX(min(window.image.width(), end.x()))
        end.setY(min(window.image.height(), end.y()))


        self.rect.setRect(QRectF(start, end))

    def finalize(self):
        end_point_mouse = QCursor.pos()
        total_mouse = end_point_mouse - self.start_point_mouse
        self.width = total_mouse.x()
        self.height = total_mouse.y()
        self.end_point = QPoint(int(self.start_point.x() + self.width), int(self.start_point.y() + self.height))
        start = QPoint(int(self.start_point.x()), int(self.start_point.y()))
        end = QPoint(int(self.end_point.x()), int(self.end_point.y()))

        if (self.width < 0):
            start.setX(self.end_point.x())
            end.setX(int(self.start_point.x()))

        if (self.height < 0):
            start.setY(self.end_point.y())
            end.setY(int(self.start_point.y()))

        start.setX(max(0, start.x()))
        start.setY(max(0, start.y()))
        end.setX(min(window.image.width(), end.x()))
        end.setY(min(window.image.height(), end.y()))

        self.start_point = start
        self.end_point = end

        self.rect.setRect(QRectF(self.start_point, self.end_point))
        self.text.setPos(self.start_point.x() - 5, self.start_point.y() - 16)
        self.text.setHtml(f"<div style='color: white; background-color: red;'>{self.label}</div>")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageDrawer()
    window.show()
    sys.exit(app.exec_())
