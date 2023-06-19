from PyQt5.QtWidgets import QGraphicsScene, QGraphicsRectItem, QMainWindow
from PyQt5.QtGui import QPen, QCursor
from PyQt5.QtCore import Qt, QRectF, QPoint


class Annotation():
    def __init__(self, start_point, end_point=None, label_id=0, label="Label"):
        # Create QGraphicsRectItem for the rectangle
        self.rect = QGraphicsRectItem()

        # Store the start and end points of the rectangle
        self.start_point = start_point
        self.end_point = end_point

        # Store the width and height of the rectangle
        self.width = None
        self.height = None

        # By default all walls are locked (Doesn't affect drawing of annotation)
        # Walls are unlocked for the resize function where it does affect drawing
        self.lock_left = self.lock_right = self.lock_up = self.lock_down = True
        self.moving = False

        # Store the label of the annotation
        self.label_id = label_id
        self.label = label

        # Store the initial mouse position
        self.start_point_mouse = QCursor.pos()

        # Set the pen properties for the rectangle
        self.pen = QPen(Qt.green)
        self.pen.setWidth(2)
        self.rect.setPen(self.pen)

        # Create a QGraphicsScene and add an empty text item
        self.scene = QGraphicsScene()
        self.scene.addText("")
        self.text = self.scene.items()[0]

        # If end_point is provided, update the rectangle and label
        if end_point is not None:
            self.update_rect(start_point, end_point)

    def update_rect(self, start_point, end_point):
        # Update the rectangle with the provided start and end points
        self.rect.setRect(QRectF(start_point, end_point))

        # Update the label position
        self.text.setPos(start_point.x() - 5, start_point.y() - 20)

        # Update the label text and style
        self.text.setHtml(f"<div style='color: white; background-color: green;' font-size: 14px;'>‎ {self.label} </div>")


    def select(self):
        # Change the pen color to green to indicate selection
        self.pen.setColor(Qt.green)
        self.rect.setPen(self.pen)

        # Update the rectangle and label with the current points and selected style
        self.update_rect(self.start_point, self.end_point)
        self.text.setHtml(f"<div style='color: white; background-color: green; font-size: 14px;'>‎ {self.label} </div>")

        # Check if the label exists in the labels.py folder and assign the necessary label identification.
        self.check_label_id()

        return True

    def deselect(self):
        # Change the pen color back to red to indicate deselection
        self.pen.setColor(Qt.red)
        self.rect.setPen(self.pen)

        # Update the rectangle and label with the current points and deselected style
        self.update_rect(self.start_point, self.end_point)
        self.text.setHtml(f"<div style='color: white; background-color: red; font-size: 14px;'>‎ {self.label} </div>")

        # Check if the label exists in the labels.py folder and assign the necessary label identification.
        self.check_label_id()

        return True

    def calculate_points(self, image_width, image_height):
        if self.moving:
            # Calculate the width and height based on the mouse position
            end_point_mouse = QCursor.pos()
            total_mouse = end_point_mouse - self.start_point_mouse
            self.width = self.end_point.x() - self.start_point.x()
            self.height = self.end_point.y() - self.start_point.y()

            startX = int(min(max(self.start_point.x() + total_mouse.x(), 0), image_width - self.width))
            endX = int(max(min(self.end_point.x() + total_mouse.x(), image_width), self.width))
            startY = int(min(max(self.start_point.y() + total_mouse.y(), 0), image_height - self.height))
            endY = int(max(min(self.end_point.y() + total_mouse.y(), image_height), self.height))

            return QPoint(startX, startY), QPoint(endX, endY)

        # Calculate the width and height based on the mouse position
        end_point_mouse = QCursor.pos()
        total_mouse = end_point_mouse - self.start_point_mouse
        self.width = total_mouse.x()
        self.height = total_mouse.y()

        if self.lock_left and self.lock_right and self.lock_up and self.lock_down:
            # Calculate the updated end point based on the width and height
            self.end_point = QPoint(int(self.start_point.x() + self.width), int(self.start_point.y() + self.height))

        # Calculate the updated start and end points for proper orientation
        start = QPoint(int(self.start_point.x()), int(self.start_point.y()))
        end = QPoint(int(self.end_point.x()), int(self.end_point.y()))

        if not self.lock_left: start.setX(start.x() + self.width)
        if not self.lock_right: end.setX(end.x() + self.width)
        if not self.lock_up: start.setY(start.y() + self.height)
        if not self.lock_down: end.setY(end.y() + self.height)

        temp_start = QPoint(int(start.x()), int(start.y()))
        temp_end = QPoint(int(end.x()), int(end.y()))

        if start.x() > end.x():
            start.setX(temp_end.x())
            end.setX(int(temp_start.x()))

        if start.y() > end.y():
            start.setY(temp_end.y())
            end.setY(int(temp_start.y()))

        # Clamp the start and end points within the image bounds
        start.setX(max(0, start.x()))
        start.setY(max(0, start.y()))
        end.setX(min(image_width, end.x()))
        end.setY(min(image_height, end.y()))

        return start, end

    def draw(self, image_width, image_height):
        # Calculate and update the points based on the final mouse position
        start_point, end_point = self.calculate_points(image_width, image_height)

        # Update the rectangle and label with the current points
        self.update_rect(start_point, end_point)

    def finish_drawing(self, image_width, image_height):
        # Calculate and update the points based on the final mouse position
        self.start_point, self.end_point = self.calculate_points(image_width, image_height)

        # Lock all walls (only important for resizing)
        self.lock_left = self.lock_right = self.lock_up = self.lock_down = True
        self.width = self.end_point.x() - self.start_point.x()
        self.height = self.end_point.y() - self.start_point.y()

        # Update the rectangle and label with the final points
        self.update_rect(self.start_point, self.end_point)

    def check_label_id(self):
        file_path = r"..\yolo\deploy\triton-inference-server\labels.py"

        with open(file_path, 'r') as file:
            labels_from_file = [line.strip() for line in file.readlines()[3:]]

        labels_dict = {}

        for index, label in enumerate(labels_from_file):
            labels_dict[label] = index

        # Access name and value of each label from the dictionary
        for label, value in labels_dict.items():
            if self.label.upper() == label.split(' =')[0].strip():
                self.label_id = int(label.split('= ')[1].strip())
                self.label = self.label.upper()
                break
            if value == 79 and self.label.upper() != label.split(' =')[0].strip():
              self.label_id = "Not included in the COCO dataset"

