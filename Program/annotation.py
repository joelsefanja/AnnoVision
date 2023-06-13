from PyQt5.QtWidgets import QGraphicsScene, QGraphicsRectItem, QMainWindow
from PyQt5.QtGui import QPen, QCursor
from PyQt5.QtCore import Qt, QRectF, QPoint


class Annotation():
    def __init__(self, start_point, end_point=None, label="Label"):
        # Create QGraphicsRectItem for the rectangle
        self.rect = QGraphicsRectItem()

        # Store the start and end points of the rectangle
        self.start_point = start_point
        self.end_point = end_point

        # Store the width and height of the rectangle
        self.width = None
        self.height = None

        # Store the label of the annotation
        self.label = label

        # Store the initial mouse position
        self.start_point_mouse = QCursor.pos()

        # Set the pen properties for the rectangle
        self.pen = QPen(Qt.red)
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
        self.text.setPos(start_point.x() - 5, start_point.y() - 16)

        # Update the label text and style
        self.text.setHtml(f"<div style='color: white; background-color: red;'>{self.label}</div>")

    def select(self):
        # Change the pen color to green to indicate selection
        self.pen.setColor(Qt.green)
        self.rect.setPen(self.pen)

        # Update the rectangle and label with the current points and selected style
        self.update_rect(self.start_point, self.end_point)
        self.text.setHtml(f"<div style='color: white; background-color: green;'>{self.label}</div>")

    def deselect(self):
        # Change the pen color back to red to indicate deselection
        self.pen.setColor(Qt.red)
        self.rect.setPen(self.pen)

        # Update the rectangle and label with the current points and deselected style
        self.update_rect(self.start_point, self.end_point)
        self.text.setHtml(f"<div style='color: white; background-color: red;'>{self.label}</div>")

    def calculate_points(self, image_width, image_height):
        # Calculate the width and height based on the mouse position
        end_point_mouse = QCursor.pos()
        total_mouse = end_point_mouse - self.start_point_mouse
        self.width = total_mouse.x()
        self.height = total_mouse.y()

        # Calculate the updated end point based on the width and height
        self.end_point = QPoint(int(self.start_point.x() + self.width), int(self.start_point.y() + self.height))

        # Calculate the updated start and end points for proper orientation
        start = QPoint(int(self.start_point.x()), int(self.start_point.y()))
        end = QPoint(int(self.end_point.x()), int(self.end_point.y()))

        if self.width < 0:
            start.setX(self.end_point.x())
            end.setX(int(self.start_point.x()))

        if self.height < 0:
            start.setY(self.end_point.y())
            end.setY(int(self.start_point.y()))

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

        # Update the rectangle and label with the final points
        self.update_rect(self.start_point, self.end_point)




