from PyQt5.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PyQt5.QtGui import QPen, QCursor
from PyQt5.QtCore import Qt, QRectF, QPoint

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

    def finalizeSelectedRegion(self):

        end_point_mouse = QCursor.pos()
        total_mouse = end_point_mouse - self.start_point_mouse

        # Calculate width and height
        self.width = total_mouse.x()
        self.height = total_mouse.y()

        # Calculate end point
        self.end_point = QPoint(int(self.start_point.x() + self.width), int(self.start_point.y() + self.height))

        # Adjust start and end points if width or height is negative
        start = QPoint(int(self.start_point.x()), int(self.start_point.y()))
        end = QPoint(int(self.end_point.x()), int(self.end_point.y()))

        if self.width < 0:
            start.setX(self.end_point.x())
            end.setX(int(self.start_point.x()))

        if self.height < 0:
            start.setY(self.end_point.y())
            end.setY(int(self.start_point.y()))

        # Clamp start and end points to image bounds
        start.setX(max(0, start.x()))
        start.setY(max(0, start.y()))
        end.setX(min(window.image.width(), end.x()))
        end.setY(min(window.image.height(), end.y()))

        # Update start and end points
        self.start_point = start
        self.end_point = end

        # Update rectangle and label
        self.rect.setRect(QRectF(self.start_point, self.end_point))
        self.text.setPos(self.start_point.x() - 5, self.start_point.y() - 16)
        self.text.setHtml(f"<div style='color: white; background-color: red;'>{self.label}</div>")