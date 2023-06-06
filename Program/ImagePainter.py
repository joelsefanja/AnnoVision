import sys, threading, math, os, cv2, subprocess
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
        self.file_path = None

        self.folder_dir = None
        self.folder_images = None
        self.folder_current_image_index = None

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

        button5 = QPushButton("Predict", self)
        button5.setIcon(QIcon('predict.png'))
        button5.clicked.connect(self.run_auto_annotate)

        button6 = QPushButton("Previous image", self)
        button6.clicked.connect(self.previous_image)

        button7 = QPushButton("Next image", self)
        button7.clicked.connect(self.next_image)

        # Add the buttons to the toolbar
        toolbar = self.addToolBar("Buttons")
        toolbar.addWidget(button1)
        toolbar.addWidget(button2)
        toolbar.addWidget(button3)
        toolbar.addWidget(button4)
        toolbar.addWidget(button5)
        toolbar.addWidget(button6)
        toolbar.addWidget(button7)

        # Create an empty label for the image
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setStyleSheet("background-color: white; border: none;")


    def open_image(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)", options=options)
        if file_path != None:
            # Load the selected image
            self.file_path = file_path
            self.image = QPixmap(file_path)

            # Calculate the new size based on the screen geometry and desired size reduction
            screen_geometry = QApplication.desktop().availableGeometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            desired_width = int(screen_width * 0.9)
            desired_height = int(screen_height * 0.9)

            # Resize the image to fit the new size while maintaining aspect ratio
            self.image = self.image.scaled(desired_width, desired_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Clear the scene and add the resized image
            self.scene.clear()
            self.scene.addPixmap(self.image)

            self.read_labels(file_path)

    def open_folder(self):
        default_dir = '/path/to/default/directory'
        options = QFileDialog.Options()
        #options |= QFileDialog.Directory
        selected_dir = QFileDialog.getExistingDirectory(window, "Select Directory", default_dir, options=options)

        if selected_dir:
            self.folder_dir = selected_dir
            self.folder_images = sorted(os.listdir(selected_dir))
            self.folder_images.pop(0)
            self.folder_current_image_index = 0

            first_image_path = os.path.join(selected_dir, self.folder_images[self.folder_current_image_index])

            self.image = QPixmap(first_image_path)
            self.scene.clear()
            self.scene.addPixmap(self.image)
            self.read_labels(first_image_path)

    def read_labels(self, image_path):
        image_dir = os.path.abspath(os.path.join(os.path.abspath(image_path), os.pardir))
        if image_path.endswith('.jpg') or image_path.endswith('.png') or image_path.endswith('.jpeg'):
            # Clear the list if another image is opened
            if len(self.preExistingAnnotations) > 0:
                self.preExistingAnnotations.clear()

            if (os.path.exists(os.path.abspath(os.path.join(image_dir, "labels", os.path.splitext(os.path.basename(image_path))[0] + ".txt")))):
                label_path = os.path.abspath(os.path.join(image_dir, "labels", os.path.splitext(os.path.basename(image_path))[0] + ".txt"))

                # Read the labels from the file
                with open(label_path, 'r') as f:
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
                    img_h = int(self.image.height())
                    img_w = int(self.image.width())
                    x1 = int((annotation[3] - annotation[5] / 2) * img_w)
                    y1 = int((annotation[4] - annotation[6] / 2) * img_h)
                    x2 = int((annotation[3] + annotation[5] / 2) * img_w)
                    y2 = int((annotation[4] + annotation[6] / 2) * img_h)

                    # Draw the bounding box on the image
                    self.currentAnnotation = Annotation(QPoint(x1, y1), QPoint(x2, y2))

                    self.annotations.append(self.currentAnnotation)
                    self.scene.addItem(self.currentAnnotation.rect)
                    self.scene.addItem(self.currentAnnotation.text)

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
            if self.action == 1:
                self.timer.stop()

                end_point = event.scenePos()
                end_point.setX(round(end_point.x() - self.image.width() / 2))
                end_point.setY(round(end_point.y() - self.image.height() / 2))
                self.currentAnnotation.finalize()

                self.annotations.append(self.currentAnnotation)
                self.scene.addItem(self.currentAnnotation.rect)
                self.scene.addItem(self.currentAnnotation.text)

    def key_press_event(self, event):
        if event.key() == Qt.Key_S and event.modifiers() == Qt.ControlModifier:
            self.action = 0
        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            self.action = 1
        if event.key() == Qt.Key_E and event.modifiers() == Qt.ControlModifier:
            self.action = 2
            if self.currentAnnotation is not None and self.line_label is None:
                self.line_label = QLineEdit(self)
                self.line_label.move(int(self.width() / 2), int(self.height() / 2))
                self.line_label.resize(80, 20)
                self.line_label.setPlaceholderText(self.currentAnnotation.label)
                self.line_label.editingFinished.connect(self.close_line_label)
                self.line_label.show()
        if event.key() == Qt.Key_D and event.modifiers() == Qt.ControlModifier:
            self.action = 3
            if self.currentAnnotation is not None:
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

    def previous_image(self):
        self.folder_current_image_index -= 1
        if (self.folder_current_image_index < 0): self.folder_current_image_index = len(self.folder_images) - 1

        image_path = os.path.join(self.folder_dir, self.folder_images[self.folder_current_image_index])
        self.image = QPixmap(image_path)
        self.scene.clear()
        self.scene.addPixmap(self.image)
        self.read_labels(image_path)

    def next_image(self):
        self.folder_current_image_index += 1
        if (self.folder_current_image_index > len(self.folder_images) - 1): self.folder_current_image_index = 0

        image_path = os.path.join(self.folder_dir, self.folder_images[self.folder_current_image_index])
        self.image = QPixmap(image_path)
        self.scene.clear()
        self.scene.addPixmap(self.image)
        self.read_labels(image_path)

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

    def run_auto_annotate(self):
        if self.file_path != None:
            subprocess_command = f"python ../yolov7/detect.py --weights ../yolov7/yolov7-tiny.pt --conf 0.25 --nosave --save-txt --source {self.file_path}"  # Replace with the actual subprocess command
            subprocess.run(subprocess_command, shell=True)
        else:
            print("No image file selected.")


class Annotation():
    def __init__(self, start_point, end_point=None, label="Label"):
        self.rect = QGraphicsRectItem()
        self.start_point = start_point
        self.end_point = end_point
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
