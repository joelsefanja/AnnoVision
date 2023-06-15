import datetime, json, shutil, subprocess, os
from pycocotools.coco import COCO
from enum import Enum
from annotation import Annotation
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QAction, \
    QFileDialog, QPushButton, QLabel, QLineEdit, QMessageBox, QInputDialog
from PyQt5.QtGui import QPixmap, QIcon, QCursor
from PyQt5.QtCore import Qt, QTimer, QPoint

class Action(Enum):
    OPEN_IMAGE = 1
    OPEN_FOLDER = 2
    PREDICT = 3
    SELECT = 4
    CREATE = 5
    RESIZE = 6
    MOVE = 7
    RENAME = 8
    DELETE = 9
    PREVIOUS = 10
    NEXT = 11
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
        self.disable_buttons(self.buttons)
        self.enable_buttons(self.open_buttons)
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
        self.action = Action.SELECT  # 0 select   1 create   2 edit   3 delete   4 resize   5 move
        self.image_path = None
        self.folder_dir = None
        self.folder_images = []
        self.folder_current_image_index = None
        self.preExistingAnnotations = []
        self.annotations = []
        self.currentAnnotation = None
        self.currentMultiAnnotations = []
        self.possibleSelectAnnotations = []
        self.selectedAnnotationIndex = 0
    def connect_mouse_events(self):
        self.scene.mousePressEvent = self.mouse_press_event
        self.scene.mouseReleaseEvent = self.mouse_release_event
        self.scene.keyPressEvent = self.key_press_event
    def create_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.drawing_annotation)
    def disable_buttons(self, buttons_group):
        for button in buttons_group:
            button.setDisabled(True)
    def enable_buttons(self, buttons_group):
        for button in buttons_group:
            button.setEnabled(True)
    def create_buttons(self):
        button_data = [
            {"label": "Open image", "icon": "../icons/open-image.png", "slot": self.open_image_file},
            {"label": "Open image folder", "icon": "../icons/folder.png", "slot": self.open_image_folder},
            {"label": "Predict", "icon": "../icons/scan.png", "slot": self.run_auto_annotate},
            {"label": "Select", "icon": "../icons/selection.png", "slot": self.action_select},
            {"label": "Create", "icon": "../icons/edit.png", "slot": self.action_create},
            {"label": "Resize", "icon": "../icons/resize.png", "slot": self.action_resize},
            {"label": "Move", "icon": "../icons/move.png", "slot": self.action_move},
            {"label": "Rename", "icon": "../icons/rename.png", "slot": self.action_rename},
            {"label": "Delete", "icon": "../icons/delete.png", "slot": self.action_delete},
            {"label": "Save to COCO", "icon": "../icons/save.png", "slot": self.save_to_COCO},
            {"label": "Previous image", "icon": "../icons/back.png", "slot": self.previous_image},
            {"label": "Next image", "icon": "../icons/next.png", "slot": self.next_image}
        ]

        self.buttons = []
        self.open_buttons = []
        self.loaded_image_buttons = []
        self.edit_annotation_buttons = []
        self.select_button = []
        self.rename_button = []
        self.delete_button = []
        self.save_coco_button = []


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

            label = button_info["label"]

            if label in ["Open image", "Open image folder"]:
                self.open_buttons.append(button)
            elif label in ["Predict", "Create", "Previous image", "Next image"]:
                self.loaded_image_buttons.append(button)
            elif label in ["Select"]:
                self.select_button.append(button)
            elif label in ["Rename","Resize", "Move", "Delete"]:
                self.edit_annotation_buttons.append(button)
            elif label in ["Rename"]:
                self.rename_button.append(button)
            elif label in ["Delete"]:
                self.delete_button.append(button)
            elif label in ["Save to COCO"]:
                self.save_coco_button.append(button)
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
    def get_label_file(self, folder_path):
        if self.image_path:
            image_files = self.get_sorted_image_files(self.folder_dir)
            image_file = os.path.normpath(self.image_path)
            image_file = image_file.replace("\\", "/")
            image_file = image_file.split(fr"{folder_path}/")[1]
            for image in image_files:
                if image_file == image:
                    label_file = image_file.split(".")[0] + ".txt"
                    label_file = os.path.join(folder_path, label_file)
            if os.path.exists(label_file):
                    self.enable_buttons(self.save_coco_button)
                    return label_file
            else:
                with open(label_file, 'w') as file:
                    self.enable_buttons(self.save_coco_button)
                return label_file
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
        pixmap_item = self.scene.addPixmap(self.image)

        # Calculate the center position of the scene
        scene_width = self.scene.width()
        scene_height = self.scene.height()
        pixmap_width = pixmap_item.pixmap().width()
        pixmap_height = pixmap_item.pixmap().height()
        center_x = (scene_width - pixmap_width) / 2
        center_y = (scene_height - pixmap_height) / 2

        # Set the position of the pixmap item to the center
        pixmap_item.setPos(center_x, center_y)

        if self.image_path:
            self.read_labels()
            self.enable_buttons(self.loaded_image_buttons)
    def read_labels(self):
        global image_path
        label_path = self.get_label_file(self.folder_dir)

        # Read the labels from the file
        with open(label_path, 'r') as f:
            lines = f.readlines()

        # Read the labels.py file containing all class names and put it into a dictionary.
        file_path = r"..\yolo\deploy\triton-inference-server\labels.py"

        with open(file_path, 'r') as file:
            labels_from_file = [line.strip() for line in file.readlines()[3:]]

        labels_dict = {}

        for index, label in enumerate(labels_from_file):
            labels_dict[label] = index

        # Process each line in the label file
        for line in lines:
            line = line.strip().split()
            if all(character.isdigit() for character in line[0]):
                # Access name and value of each label from the dictionary
                for label, value in labels_dict.items():
                    class_id = int(line[0])
                    if class_id == value:
                        class_name = label.replace(f' = {class_id}', '')
                        break
                x, y, w, h = map(float, line[1:5])
            else:
                first_string = ""
                # Combine consecutive string elements until an integer is encountered
                for element in line:
                    if element.isalpha():
                        # Add the element to the first_string
                        first_string += element + ' '
                    else:
                        # Stop adding to the first_string and start separating the integers
                        break

                # Remove trailing whitespace from first_string
                first_string = first_string.strip()

                # Process the remaining elements as separate lines
                additional_lines = line[len(first_string.split()):]

                class_id = "Not in COCO dataset"
                class_name = first_string

                if self.preExistingAnnotations:
                    self.enable_buttons(self.select_button)
                else:
                    self.disable_buttons(self.edit_annotation_buttons + self.select_button)

                for annotation in self.preExistingAnnotations:
                    img_h = int(self.image.height())
                    img_w = int(self.image.width())
                    x1 = int((x - w / 2) * img_w)
                    y1 = int((y - h / 2) * img_h)
                    x2 = int((x + w / 2) * img_w)
                    y2 = int((y + h / 2) * img_h)

                    # Add the annotation to the class and draw the item.
                    self.currentAnnotation = Annotation(QPoint(x1, y1), QPoint(x2, y2), class_id, class_name)

                    self.annotations.append(self.currentAnnotation)
                    self.scene.addItem(self.currentAnnotation.rect)
                    self.scene.addItem(self.currentAnnotation.text)
    def modify_txt_file(self):
        global image_path
        # image_path = self.get_image_path()
        label_path = self.get_label_file(self.folder_dir)
        # image_dir = os.path.abspath(os.path.join(os.path.abspath(image_path), os.pardir))
        # label_path = os.path.abspath(os.path.join(image_dir, os.path.splitext(os.path.basename(image_path))[0] + ".txt"))
        image_width = int(self.image.width())
        image_height = int(self.image.height())

        if len(self.annotations) == 0:
            self.read_labels()

        # Clear the .txt file, so it can be overwritten.
        with open(label_path, 'w') as file:
            pass

        # Modify the annotations as needed
        for annotation in self.annotations:

            # Convert the coordinates back to YoloV7 format
            x = (annotation.start_point.x() + annotation.end_point.x()) / (2 * image_width)
            y = (annotation.start_point.y() + annotation.end_point.y()) / (2 * image_height)
            w = (annotation.end_point.x() - annotation.start_point.x()) / image_width
            h = (annotation.end_point.y() - annotation.start_point.y()) / image_height

            # Write the old + new annotations to the .txt file
            with open(label_path, 'a') as file:
                if isinstance(annotation.label_id, str):
                    line = f"{annotation.label} {x} {y} {w} {h}\n"
                    file.write(line)
                else:
                    line = f"{annotation.label_id} {x} {y} {w} {h}\n"
                    file.write(line)
    def save_to_COCO(self):
        image_path = self.image_path
        # This prevents the button activating the image if there currently is no image loaded.
        if image_path is not None:
            # Assign the necessary variables for the COCO dataset.
            image_width = int(self.image.width())
            image_height = int(self.image.height())
            image_id = 0
            annotation_id = 0
            area = image_width * image_height
            segmentation = "Bounding Box"

            # Construct the file paths
            current_directory = os.getcwd()
            parent_directory = os.path.dirname(current_directory)
            COCO_images = os.path.join(parent_directory, 'COCO', 'Images')
            COCO_annotations = os.path.join(parent_directory, 'COCO', 'Annotations')

            # Check if the directories exists and determine the image_id, if not then create the directory
            if os.path.exists(COCO_images):
                for item in os.listdir(COCO_images):
                    item_path = os.path.join(COCO_annotations, item)
                    if item_path:
                        image_id += 1
            else:
                directory = COCO_annotations
                os.makedirs(directory, exist_ok=True)
                directory = COCO_images
                os.makedirs(directory, exist_ok=True)

            # Create an empty COCO object
            coco = COCO()

            # Create the dataset and write to it
            coco.dataset = {
                "images": [],
                "annotations": [],
                "categories": []
            }

            images = {
                "id": image_id,
                "width": image_width,
                "height": image_height,
                "file_name": image_path
            }
            coco.dataset["images"].append(images)

            for annotation in self.annotations:
                x1 = annotation.start_point.x()
                y1 = annotation.start_point.y()
                x2 = annotation.end_point.x()
                y2 = annotation.end_point.y()
                category_id = annotation.label_id
                category_name = annotation.label

                annotation = {
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": category_id,
                    "category_name": category_name,
                    "segmentation": segmentation,
                    "bbox": (x1, y1, x2, y2),
                    "area": area,
                }
                coco.dataset["annotations"].append(annotation)
                annotation_id += 1

            for annotation in self.annotations:
                id = annotation.label_id
                name = annotation.label

                # Prevents duplicates from being written in the file.
                if any(category['name'] == name for category in coco.dataset["categories"]):
                    continue

                category = {
                    "id": id,
                    "name": name,
                }
                coco.dataset["categories"].append(category)

            # Create a timestamp for each json file.
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

            # Save the dataset to a json file
            annotation_file = os.path.join(COCO_annotations, f'Annotations_{timestamp}.json')
            with open(annotation_file, 'w') as json_file:
                json.dump(coco.dataset, json_file, indent=4)

            # Save the image to the COCO\Images folder
            image_type = self.get_image_type()
            image_name = f'{image_id}{image_type}'
            save_path = os.path.join(COCO_images, image_name)
            shutil.copy2(image_path, save_path)

            if self.annotations:
                # Confirmation of the process being completed.
                # Also prevents the function from being activated multiple times through spam
                msg_box = QMessageBox()
                msg_box.setWindowTitle("Annotations saved")
                msg_box.setText(f"Annotations are saved at {parent_directory}/{image_name}.txt")
                msg_box.exec_()
            if not self.annotations:
                # Confirmation of the process being completed.
                # Also prevents the function from being activated multiple times through spam
                msg_box = QMessageBox()
                msg_box.setWindowTitle("No annotation")
                msg_box.setText("Their are no annotations to be saved. \nPlease make some annotations first")
                msg_box.exec_()
    def get_image_type(self):
        # Checks the filetype of the current image, so that it can be saved in the same format.
        file_extension = os.path.splitext(self.image_path)[1].lower()
        if file_extension == '.jpg' or file_extension == '.jpeg':
            return '.jpeg'
        elif file_extension == '.png':
            return '.png'
        else:
            return 'False'
    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)
    def mouse_press_event(self, event):
        # Check if the left mouse button is pressed and there is an image available
        if event.button() == Qt.LeftButton and self.image and event.type() == event.GraphicsSceneMousePress:
            if self.action == Action.CREATE:
                mouse_pos = event.scenePos()

                # Find all annotations at the mouse position
                annotations = [annotation for annotation in self.annotations if annotation.rect.contains(mouse_pos)]

                if self.currentMultiAnnotations:
                    # Deselect all currently selected multi-annotations
                    for anno in self.currentMultiAnnotations:
                        anno.deselect()
                    self.currentMultiAnnotations = []

                if self.currentAnnotation:
                    # Deselect the current annotation if any
                    self.currentAnnotation.deselect()

                if annotations:
                    if self.currentAnnotation in annotations:
                        # If the current annotation is in the list of overlapping annotations,
                        # move to the next one in a circular manner
                        index = annotations.index(self.currentAnnotation)
                        self.currentAnnotation = annotations[(index + 1) % len(annotations)]
                        self.currentAnnotation.select()
                        self.enable_buttons(self.edit_annotation_buttons)
                        print("Next annotation selected.")
                    else:
                        # If the current annotation is not in the list of overlapping annotations,
                        # select the first annotation from the list
                        self.currentAnnotation = annotations[0]
                        self.currentAnnotation.select()
                        self.enable_buttons(self.edit_annotation_buttons)
                        print("Annotation selected.")
                else:
                    # No annotations at the mouse position, clear the current annotation
                    self.currentAnnotation = None
                    self.disable_buttons(self.edit_annotation_buttons)
                    print("Annotation deselected.")

            if self.action == Action.CREATE:
                self.view.setCursor(Qt.CrossCursor)
                if self.currentMultiAnnotations:
                    for anno in self.currentMultiAnnotations:
                        anno.deselect()
                    self.currentMultiAnnotations = []
                    self.disable_buttons(self.edit_annotation_buttons + self.select_button)
                if self.currentAnnotation:
                    self.currentAnnotation.deselect()
                    self.disable_buttons(self.edit_annotation_buttons + self.select_button)

                start_point = event.scenePos()
                start_point.setX(round(start_point.x()))
                start_point.setY(round(start_point.y()))

                self.currentAnnotation = Annotation(start_point)
                self.drawing_annotation()
                self.timer.start(16)

            if self.action == Action.RESIZE:
                if self.currentAnnotation:
                    marge = 10
                    mouse_pos = event.scenePos()
                    annotation = self.currentAnnotation
                    lock_left = annotation.start_point.x() - marge < mouse_pos.x() < annotation.start_point.x() + marge
                    lock_right = annotation.end_point.x() - marge < mouse_pos.x() < annotation.end_point.x() + marge
                    lock_up = annotation.start_point.y() - marge < mouse_pos.y() < annotation.start_point.y() + marge
                    lock_down = annotation.end_point.y() - marge < mouse_pos.y() < annotation.end_point.y() + marge

                    if lock_left:
                        annotation.lock_left = False
                        self.view.setCursor(Qt.SizeHorCursor)
                    if lock_right:
                        annotation.lock_left = True
                        annotation.lock_right = False
                        self.view.setCursor(Qt.SizeHorCursor)
                    if lock_up:
                        annotation.lock_up = False
                        self.view.setCursor(Qt.SizeVerCursor)
                    if lock_down:
                        annotation.lock_up = True
                        annotation.lock_down = False
                        self.view.setCursor(Qt.SizeVerCursor)

                    if not (lock_right and lock_down) or not (lock_left and lock_up):
                        self.view.setCursor(Qt.SizeBDiagCursor)

                    if not (lock_right and lock_up) or not (lock_left and lock_down):
                        self.view.setCursor(Qt.SizeFDiagCursor)

                    if not (lock_left and lock_right and lock_up and lock_down):
                        annotation.start_point_mouse = QCursor.pos()
                        self.drawing_annotation()
                        self.timer.start(16)

            if self.action == Action.MOVE:
                if self.currentAnnotation and not self.currentMultiAnnotations:
                    self.view.setCursor(Qt.SizeAllCursor)
                    mouse_pos = event.scenePos()
                    annotation = self.currentAnnotation
                    annotation.moving = True
                    annotation.start_point_mouse = QCursor.pos()
                    self.drawing_annotation()
                    self.timer.start(16)

    def mouse_release_event(self, event):
        if event.button() == Qt.LeftButton and self.image:
            if self.action == Action.CREATE:
                if self.currentAnnotation:
                    self.view.setCursor(Qt.ArrowCursor)
                    self.timer.stop()
                    self.currentAnnotation.finish_drawing(self.image.width(), self.image.height())

                    self.annotations.append(self.currentAnnotation)
                    self.scene.addItem(self.currentAnnotation.rect)
                    self.scene.addItem(self.currentAnnotation.text)

            if self.action == Action.RESIZE:
                if self.currentAnnotation:
                    self.view.setCursor(Qt.ArrowCursor)
                    if not self.currentAnnotation.lock_left == self.currentAnnotation.lock_right == self.currentAnnotation.lock_up == self.currentAnnotation.lock_down == True:
                        self.timer.stop()
                        self.currentAnnotation.finish_drawing(self.image.width(), self.image.height())

            if self.action == Action.MOVE:
                if self.currentAnnotation:
                    self.view.setCursor(Qt.ArrowCursor)
                    self.timer.stop()
                    self.currentAnnotation.finish_drawing(self.image.width(), self.image.height())
                    self.currentAnnotation.moving = False
    def select_all_annotations(self):
       self.currentMultiAnnotations = self.annotations[:]
       if(self.currentMultiAnnotations):
           self.enable_buttons(self.rename_button + self.delete_button)
       for anno in self.currentMultiAnnotations:
           anno.select()
    def key_press_event(self, event):
        if event.key() == Qt.Key_Left:
            self.previous_image()
        elif event.key() == Qt.Key_Right:
            self.next_image()
        else:
            super().keyPressEvent(event)
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_S:
                self.action_select()
            elif event.key() == Qt.Key_C:
                self.action_create()
            #elif event.key() == Qt.Key_E:
             #   self.handle_edit_action()
            elif event.key() == Qt.Key_D:
                self.action_delete()
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
            elif event.key() == Qt.Key_A:
                self.select_all_annotations()
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
        self.action = Action.SELECT
    def action_create(self):
        self.action = Action.CREATE
    def action_resize(self):
        self.action = Action.RESIZE
    def action_move(self):
        self.action = Action.MOVE

    def action_rename(self):
        self.action = Action.RENAME

        self.line_label = QLineEdit(self)
        self.line_label.move(int(self.width() / 2), int(self.height() / 2))
        self.line_label.resize(80, 20)
        self.line_label.setPlaceholderText(self.currentAnnotation.label)
        self.line_label.editingFinished.connect(self.close_line_label)
        self.line_label.show()


    def action_delete(self):
        self.action = Action.DELETE
        if (self.currentAnnotation != None):
            anno = self.annotations.pop(self.annotations.index(self.currentAnnotation))
            self.scene.removeItem(anno.rect)
            self.scene.removeItem(anno.text)
            self.currentAnnotation = None
            self.disable_buttons(self.edit_annotation_buttons)

        if (self.currentMultiAnnotations):
            for anno in self.currentMultiAnnotations:
                self.scene.removeItem(anno.rect)
                self.scene.removeItem(anno.text)
            self.currentMultiAnnotations = []
            self.disable_buttons(self.edit_annotation_buttons)
            self.disable_buttons(self.select_button)
        if not self.annotations:
            self.disable_buttons(self.edit_annotation_buttons + self.select_button)
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

        # Check if there are annotations for the current image
        if len(self.annotations) > 0:
            self.enable_buttons(self.select_button)
        else:
            self.disable_buttons(self.edit_annotation_buttons)
            self.disable_buttons(self.select_button)
    def previous_image(self):
        # Check if the current image index is not set
        if self.folder_current_image_index is None:
            return

        # Decrement the current image index
        self.folder_current_image_index -= 1
        # Wrap around to the last image if the index goes below zero
        if self.folder_current_image_index < 0:
            self.folder_current_image_index = len(self.folder_images) - 1

        # Update the .txt annotations file
        self.modify_txt_file()

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

        # Update the .txt annotations file
        self.modify_txt_file()

        # Update the displayed image
        self.image_path = os.path.join(self.folder_dir, self.folder_images[self.folder_current_image_index])
        self.update_image()

    def close_line_label(self):
        new_label = self.line_label.text()

        if self.currentAnnotation is not None:
            self.currentAnnotation.label = new_label
            self.currentAnnotation.select()
            self.currentAnnotation.text.setPlainText(new_label)

        if self.currentMultiAnnotations:
            for annotation in self.currentMultiAnnotations:
                annotation.label = new_label
                annotation.deselect()
                annotation.text.setPlainText(new_label)

        self.line_label.close()
        self.line_label = None
        self.currentMultiAnnotations = []

        font_size = '16px'  # Adjust the font size as desired
        font_weight = 'bold'  # Set to 'bold' for bold text

        self.setStyleSheet(f"QLineEdit {{ font-size: {font_size}; font-weight: {font_weight}; }}")

    def drawing_annotation(self):
        self.currentAnnotation.draw(self.image.width(), self.image.height())
        self.scene.addItem(self.currentAnnotation.rect)
        if self.annotations is not None:
            self.enable_buttons(self.select_button + self.edit_annotation_buttons)
    def run_auto_annotate(self):
        if self.image_path != None:
            subprocess_command = f"python ../yolo/detect.py --weights ../yolov7/yolov7-tiny.pt --conf 0.25 --nosave --save-txt --source {self.image_path} --name {self.image_path}"
            subprocess.run(subprocess_command, shell=True)
            self.update_image()
        else:
            print("No image file selected.")




