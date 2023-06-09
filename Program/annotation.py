from PyQt5.QtWidgets import QGraphicsScene, QGraphicsRectItem, QMainWindow
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
                self.currentAnnotation.finalizeSelectedRegion()

                self.annotations.append(self.currentAnnotation)
                self.scene.addItem(self.currentAnnotation.rect)
                self.scene.addItem(self.currentAnnotation.text)
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

    def draw(self, start_point, end_point, image_width, image_height):
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
        end.setX(min(image_width, end.x()))
        end.setY(min(image_height, end.y()))

        self.rect.setRect(QRectF(start, end))

    def finalizeSelectedRegion(self, start_point, end_point, image_width, image_height):
        end_point_mouse = QCursor.pos()
        total_mouse = end_point_mouse - self.start_point_mouse

        # Calculate width and height
        self.width = total_mouse.x()
        self.height = total_mouse.y()

        # Calculate end point
        self.end_point = QPoint(int(start_point.x() + self.width), int(start_point.y() + self.height))

        # Adjust start and end points if width or height is negative
        start = QPoint(int(start_point.x()), int(start_point.y()))
        end = QPoint(int(self.end_point.x()), int(self.end_point.y()))

        if self.width < 0:
            start.setX(self.end_point.x())
            end.setX(int(start_point.x()))

        if self.height < 0:
            start.setY(self.end_point.y())
            end.setY(int(start_point.y()))

        # Clamp start and end points to image bounds
        start.setX(max(0, start.x()))
        start.setY(max(0, start.y()))
        end.setX(min(image_width, end.x()))
        end.setY(min(image_height, end.y()))

        # Update start and end points
        self.start_point = start
        self.end_point = end

        # Update rectangle and label
        self.rect.setRect(QRectF(self.start_point, self.end_point))
        self.text.setPos(self.start_point.x() - 5, self.start_point.y() - 16)
        self.text.setHtml(f"<div style='color: white; background-color: red;'>{self.label}</div>")
