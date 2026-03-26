from PySide6.QtWidgets import QGraphicsScene, QGraphicsView
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPen, QColor, QPainter, QWheelEvent, QPixmap


class VenueGraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_size = 0.5  # meters
        self.setSceneRect(-50, -50, 100, 100)  # 100m x 100m default
        self._background_pixmap = None

    def set_background_image(self, path: str) -> None:
        self._background_pixmap = QPixmap(path)
        self.update()

    def clear_background_image(self) -> None:
        self._background_pixmap = None
        self.update()

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        super().drawBackground(painter, rect)

        # Draw background image if set
        if self._background_pixmap and not self._background_pixmap.isNull():
            painter.setOpacity(0.3)
            painter.drawPixmap(self.sceneRect().toRect(), self._background_pixmap)
            painter.setOpacity(1.0)

        # Draw grid
        pen = QPen(QColor(200, 200, 200), 0)
        painter.setPen(pen)

        left = int(rect.left() / self.grid_size) * self.grid_size
        top = int(rect.top() / self.grid_size) * self.grid_size

        x = left
        while x <= rect.right():
            painter.drawLine(int(x * 100) / 100, rect.top(), int(x * 100) / 100, rect.bottom())
            x += self.grid_size

        y = top
        while y <= rect.bottom():
            painter.drawLine(rect.left(), int(y * 100) / 100, rect.right(), int(y * 100) / 100)
            y += self.grid_size

        # Draw origin axes
        axis_pen = QPen(QColor(150, 150, 150), 0.02)
        painter.setPen(axis_pen)
        painter.drawLine(rect.left(), 0, rect.right(), 0)
        painter.drawLine(0, rect.top(), 0, rect.bottom())


class VenueGraphicsView(QGraphicsView):
    mouse_moved = Signal(float, float)  # emits scene coords in meters

    def __init__(self, scene: VenueGraphicsScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self._panning = False
        self._pan_start = None
        # Scale: 1 scene unit = 1 meter. Initial zoom: ~50 pixels per meter
        self.scale(50, 50)

    def wheelEvent(self, event: QWheelEvent) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._panning and self._pan_start is not None:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
        else:
            super().mouseMoveEvent(event)
        # Emit mouse position in scene coordinates
        scene_pos = self.mapToScene(event.position().toPoint())
        self.mouse_moved.emit(scene_pos.x(), scene_pos.y())
