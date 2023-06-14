import subprocess, os
from enum import Enum
from annotation import Annotation
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QAction, \
    QFileDialog, QPushButton, QLabel, QLineEdit
from PyQt5.QtGui import QPixmap, QIcon, QCursor
from PyQt5.QtCore import Qt, QTimer, QPoint

class Action(Enum):
    OPEN = 1
    SAVE = 2
    COPY = 3
    PASTE = 4
    UNDO = 5
    REDO = 6

class ImageDrawer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setup_ui()
        self.create_graphics_view()
        self.initialize_variables()
        # self.create_menu_bar()
        self.connect_mouse_events()
        self.create_timer()
        self.create_buttons()
        self.create_toolbar()
        self.image_label = self.create_image_label()

    def setup_ui(self):
        self.setWindowTitle("AnnoVision")
        self.setWindowState(Qt.WindowMaximized)

    def create_graphics_view(self):
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)

    def initialize_variables(self):
        self.image = None
        self.line_label = None
        self.action = 0  # 0 select   1 create   2 edit   3 delete   4 resize
        self.image_path = None
        self.folder_dir = None
        self.folder_images = []
        self.folder_current_image_index = None
        self.preExistingAnnotations = []
        self.annotations = []
        self.currentAnnotation = None
        self.possibleSelectAnnotations = []
        self.selectedAnnotationIndex = 0

    def connect_mouse_events(self):
        self.scene.mousePressEvent = self.mouse_press_event
        self.scene.mouseReleaseEvent = self.mouse_release_event
        self.scene.keyPressEvent = self.key_press_event

    def create_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.drawing_annotation)

    def create_buttons(self):
        button_data = [
            {"label": "Open image", "icon": "../icons/open-image.png", "slot": self.open_image_file},
            {"label": "Open image folder", "icon": "../icons/folder.png", "slot": self.open_image_folder},
            {"label": "Select", "icon": "../icons/cursor.png", "slot": self.action_select},
            {"label": "Create", "icon": "../icons/box.png", "slot": self.action_create},
            {"label": "Resize", "icon": "../icons/box.png", "slot": self.action_resize},
            {"label": "Label", "icon": "../icons/font.png", "slot": self.action_label},
            {"label": "Delete", "icon": "../icons/delete.png", "slot": self.action_delete},
            {"label": "Predict", "icon": "../icons/scan.png", "slot": self.run_auto_annotate},
            {"label": "Previous image", "icon": "../icons/back.png", "slot": self.previous_image},
            {"label": "Next image", "icon": "../icons/next.png", "slot": self.next_image}
        ]

        self.buttons = []

        for button_info in button_data:
            button = QPushButton(button_info["label"], self)
            icon = button_info["icon"]
            slot = button_info["slot"]

            if icon:
                button.setIcon(QIcon(icon))
            button.clicked.connect(slot)

            # Set padding and font size using style sheets
            button.setStyleSheet("""
                QPushButton {
                    padding: 10px;
                    font-size: 16px;
                }
            """)

            self.buttons.append(button)

    def create_toolbar(self):
        toolbar = self.addToolBar("buttons")

        for button in self.buttons:
            toolbar.addWidget(button)

    def create_image_label(self):
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumSize(400, 400)
        image_label.setStyleSheet("background-color: white; border: none;")
        return image_label

    def reset_annotations(self):
        # Reset the annotations
        self.preExistingAnnotations = []
        self.annotations = []
        self.currentAnnotation = None

    def open_image_file(self):
        # Reset annotations when opening an image file
        self.reset_annotations()

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg)",
                                                   options=options)

        if file_path:
            self.folder_dir = os.path.dirname(file_path)
            self.update_folder_state()
            self.image_path = file_path
            self.update_image()  # Call update_image function

    def open_image_folder(self):
        # Reset annotations when opening an image folder
        self.reset_annotations()

        options = QFileDialog.Options()
        folder_dir = QFileDialog.getExistingDirectory(self, 'Select Folder')

        if folder_dir:
            self.folder_dir = folder_dir
            self.update_folder_state()

    def update_folder_state(self):
        # Update the folder state
        self.folder_images = self.get_sorted_image_files(self.folder_dir)
        self.folder_current_image_index = 0  # Open the first (newest) image in the folder
        self.image_path = self.get_image_path(self.folder_dir, self.folder_images[self.folder_current_image_index])
        self.update_image()

    def get_sorted_image_files(self, folder_path):
        included_extensions = ['jpg', 'jpeg', 'png']
        image_files = [file for file in os.listdir(folder_path)
                       if any(file.endswith(ext) for ext in included_extensions)]
        return image_files

    def get_image_path(self, folder_path, image_file):
        return os.path.join(folder_path, image_file)

    def resize_and_display_image(self):
        screen_geometry = QApplication.desktop().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        desired_width = int(screen_width * 0.9)
        desired_height = int(screen_height * 0.9)

        self.image = self.image.scaled(desired_width, desired_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.scene.clear()
        self.scene.addPixmap(self.image)

        if self.image_path:
            self.read_labels(self.image_path)

    def read_labels(self, image_path):
        image_dir = os.path.abspath(os.path.join(os.path.abspath(image_path), os.pardir))
        if image_path.endswith('.jpg') or image_path.endswith('.png') or image_path.endswith('.jpeg'):
            # Clear the list if another image is opened
            if len(self.preExistingAnnotations) > 0:
                self.preExistingAnnotations.clear()

            if (os.path.exists(os.path.abspath(os.path.join(image_dir, os.path.splitext(os.path.basename(image_path))[0] + ".txt")))):
                label_path = os.path.abspath(os.path.join(image_dir, os.path.splitext(os.path.basename(image_path))[0] + ".txt"))

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

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)

    def mouse_press_event(self, event):
        if event.button() == Qt.LeftButton and self.image and event.type() == event.GraphicsSceneMousePress:
            if self.action == 0:
                mouse_pos = event.scenePos()

                # Find all annotations at the mouse position
                annotations = [annotation for annotation in self.annotations if annotation.rect.contains(mouse_pos)]

                if self.currentAnnotation:
                    self.currentAnnotation.deselect()

                if annotations:
                    if self.currentAnnotation in annotations:
                        # If the current annotation is in the list of overlapping annotations,
                        # move to the next one
                        index = annotations.index(self.currentAnnotation)
                        self.currentAnnotation = annotations[(index + 1) % len(annotations)]
                        self.currentAnnotation.select()
                    else:
                        # If the current annotation is not in the list of overlapping annotations,
                        # select the first annotation from the list
                        self.currentAnnotation = annotations[0]
                        self.currentAnnotation.select()
                else:
                    self.currentAnnotation = None

            if self.action == 1:
                if self.currentAnnotation:
                    self.currentAnnotation.deselect()

                start_point = event.scenePos()
                start_point.setX(round(start_point.x()))
                start_point.setY(round(start_point.y()))

                self.currentAnnotation = Annotation(start_point)
                self.drawing_annotation()
                self.timer.start(16)

            if self.action == 4:
                if self.currentAnnotation:
                    mouse_pos = event.scenePos()
                    if self.currentAnnotation.start_point.x() - 5 < mouse_pos.x() < self.currentAnnotation.start_point.x() + 5:
                        self.currentAnnotation.lock_left = False
                    if self.currentAnnotation.end_point.x() - 5 < mouse_pos.x() < self.currentAnnotation.end_point.x() + 5:
                        self.currentAnnotation.lock_left = True
                        self.currentAnnotation.lock_right = False
                    if self.currentAnnotation.start_point.y() - 5 < mouse_pos.y() < self.currentAnnotation.start_point.y() + 5:
                        self.currentAnnotation.lock_up = False
                    if self.currentAnnotation.end_point.y() - 5 < mouse_pos.y() < self.currentAnnotation.end_point.y() + 5:
                        self.currentAnnotation.lock_up = True
                        self.currentAnnotation.lock_down = False

                    if not self.currentAnnotation.lock_left == self.currentAnnotation.lock_right == self.currentAnnotation.lock_up == self.currentAnnotation.lock_down == True:
                        self.currentAnnotation.start_point_mouse = QCursor.pos()
                        self.drawing_annotation()
                        self.timer.start(16)

    def mouse_release_event(self, event):
        if event.button() == Qt.LeftButton and self.image:
            if self.action == 1: # Create
                if self.currentAnnotation:
                    self.timer.stop()
                    self.currentAnnotation.finish_drawing(self.image.width(), self.image.height())

                    self.annotations.append(self.currentAnnotation)
                    self.scene.addItem(self.currentAnnotation.rect)
                    self.scene.addItem(self.currentAnnotation.text)

            if self.action == 4: # Resize
                if self.currentAnnotation:
                    if not self.currentAnnotation.lock_left == self.currentAnnotation.lock_right == self.currentAnnotation.lock_up == self.currentAnnotation.lock_down == True:
                        self.timer.stop()
                        self.currentAnnotation.finish_drawing(self.image.width(), self.image.height())

    def key_press_event(self, event):
        if event.key() == Qt.Key_Left:
            self.previous_image()
        elif event.key() == Qt.Key_Right:
            self.next_image()
        else:
            super().keyPressEvent(event)
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_S:
                self.set_action(0)
            elif event.key() == Qt.Key_C:
                self.set_action(1)
            elif event.key() == Qt.Key_E:
                self.set_action(2)
                self.handle_edit_action()
            elif event.key() == Qt.Key_D:
                self.set_action(3)
                self.handle_delete_action()
            elif event.key() == Qt.Key_O:
                self.open_image_file()
            elif event.key() == Qt.Key_BracketLeft:
                self.zoom_out()
            elif event.key() == Qt.Key_BracketRight:
                self.zoom_in()
            elif event.key() == Qt.Key_Equal:
                self.zoom_in()
            elif event.key() == Qt.Key_Minus:
                self.zoom_out()
            elif event.key() == Qt.Key_F:
                self.open_image_folder()
            elif event.key() == Qt.Key_Left:
                self.previous_image()
            elif event.key() == Qt.Key_Right:
                self.next_image()
        else:
            if event.key() == Qt.Key_Left:
                self.previous_image()
            elif event.key() == Qt.Key_Right:
                self.next_image()

    def zoom_in(self):
        if self.image:
            self.view.scale(1.1, 1.1)

    def zoom_out(self):
        if self.image:
            self.view.scale(0.9, 0.9)

    def action_select(self):
        self.action = 0

    def action_create(self):
        self.action = 1

    def action_resize(self):
        self.action = 4

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

    def update_image(self):
        # Reset annotations
        self.preExistingAnnotations = []
        self.annotations = []
        self.currentAnnotation = None

        # Build the path to the current image
        # image_path = os.path.join(self.folder_dir, self.folder_images[self.folder_current_image_index])

        # Load the image and display it in the scene
        self.image = QPixmap(self.image_path)
        self.scene.clear()
        self.scene.addPixmap(self.image)

        # Read labels associated with the image
        self.resize_and_display_image()

    def previous_image(self):
        # Check if the current image index is not set
        if self.folder_current_image_index is None:
            return

        # Decrement the current image index
        self.folder_current_image_index -= 1
        # Wrap around to the last image if the index goes below zero
        if self.folder_current_image_index < 0:
            self.folder_current_image_index = len(self.folder_images) - 1

        # Update the displayed image
        self.image_path = os.path.join(self.folder_dir, self.folder_images[self.folder_current_image_index])
        self.update_image()

    def next_image(self):
        # Check if the current image index is not set
        if self.folder_current_image_index is None:
            return

        # Increment the current image index
        self.folder_current_image_index += 1
        # Wrap around to the first image if the index goes beyond the last image
        if self.folder_current_image_index >= len(self.folder_images):
            self.folder_current_image_index = 0

        # Update the displayed image
        self.image_path = os.path.join(self.folder_dir, self.folder_images[self.folder_current_image_index])
        self.update_image()

    def close_line_label(self):
        if (self.line_label != None and self.currentAnnotation != None):
            self.currentAnnotation.label = self.line_label.text()
            self.currentAnnotation.deselect()
            self.line_label.close()
            self.line_label = None
            self.currentAnnotation = None

    def drawing_annotation(self):
        self.currentAnnotation.draw(self.image.width(), self.image.height())
        self.scene.addItem(self.currentAnnotation.rect)

    def run_auto_annotate(self):
        if self.image_path != None:
            subprocess_command = f"python ../yolov7/detect.py --weights ../yolov7/yolov7-tiny.pt --conf 0.25 --nosave --save-txt --source {self.image_path} --name {self.image_path}"
            subprocess.run(subprocess_command, shell=True)
            self.update_image()
        else:
            print("No image file selected.")
