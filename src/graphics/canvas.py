from __future__ import annotations
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsLineItem
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPen, QColor, QPainter, QWheelEvent, QPixmap

from src.widgets.toolbar import ToolMode
from src.graphics.wall_item import WallItem
from src.graphics.obstacle_item import ObstacleItem
from src.graphics.region_item import RegionItem
from src.models.region import Region


class VenueGraphicsScene(QGraphicsScene):
    wall_finished = Signal(object)       # emits WallItem
    obstacle_finished = Signal(object)   # emits ObstacleItem
    region_moved = Signal(str)           # emits region name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_size = 0.5  # meters
        self.setSceneRect(-50, -50, 100, 100)  # 100m x 100m default
        self._background_pixmap = None

        self._tool_mode = ToolMode.SELECT
        self._snap_to_grid = True
        self._drawing_points: list[QPointF] = []
        self._preview_item = None  # live polygon preview while drawing
        self._preview_line = None  # line from last point to cursor

    def set_tool_mode(self, mode: ToolMode) -> None:
        if self._tool_mode != mode:
            self._cancel_drawing()
        self._tool_mode = mode

    def set_background_image(self, path: str) -> None:
        self._background_pixmap = QPixmap(path)
        self.update()

    def clear_background_image(self) -> None:
        self._background_pixmap = None
        self.update()

    # --- Drawing interaction ---

    def handle_left_click(self, scene_pos: QPointF) -> None:
        if self._tool_mode in (ToolMode.WALL, ToolMode.OBSTACLE):
            self._add_drawing_point(scene_pos)

    def handle_double_click(self, scene_pos: QPointF) -> None:
        if self._tool_mode in (ToolMode.WALL, ToolMode.OBSTACLE):
            self._finish_drawing()

    def handle_right_click(self, scene_pos: QPointF) -> None:
        if self._tool_mode in (ToolMode.WALL, ToolMode.OBSTACLE):
            self._cancel_drawing()

    def handle_mouse_move(self, scene_pos: QPointF) -> None:
        if self._tool_mode in (ToolMode.WALL, ToolMode.OBSTACLE) and self._drawing_points:
            self._update_preview_line(scene_pos)

    def _add_drawing_point(self, pos: QPointF) -> None:
        self._drawing_points.append(pos)
        self._update_preview_polygon()

    def _finish_drawing(self) -> None:
        if len(self._drawing_points) >= 3:
            if self._tool_mode == ToolMode.WALL:
                item = WallItem(self._drawing_points)
                self.addItem(item)
                self.wall_finished.emit(item)
            elif self._tool_mode == ToolMode.OBSTACLE:
                item = ObstacleItem(self._drawing_points)
                self.addItem(item)
                self.obstacle_finished.emit(item)
        self._clear_preview()
        self._drawing_points = []

    def _cancel_drawing(self) -> None:
        self._clear_preview()
        self._drawing_points = []

    def _update_preview_polygon(self) -> None:
        if self._preview_item:
            self.removeItem(self._preview_item)
            self._preview_item = None
        if len(self._drawing_points) >= 2:
            if self._tool_mode == ToolMode.WALL:
                self._preview_item = WallItem(self._drawing_points)
                self._preview_item.setPen(QPen(QColor(0, 0, 0, 128), 0.03, Qt.PenStyle.DashLine))
            else:
                self._preview_item = ObstacleItem(self._drawing_points)
                self._preview_item.setPen(QPen(QColor(100, 100, 100, 128), 0.03, Qt.PenStyle.DashLine))
            self._preview_item.setFlag(WallItem.GraphicsItemFlag.ItemIsSelectable, False)
            self.addItem(self._preview_item)

    def _update_preview_line(self, cursor_pos: QPointF) -> None:
        if self._preview_line:
            self.removeItem(self._preview_line)
            self._preview_line = None
        if self._drawing_points:
            last = self._drawing_points[-1]
            line = QGraphicsLineItem(last.x(), last.y(), cursor_pos.x(), cursor_pos.y())
            line.setPen(QPen(QColor(100, 100, 100, 128), 0.02, Qt.PenStyle.DashLine))
            self._preview_line = line
            self.addItem(line)

    def _clear_preview(self) -> None:
        if self._preview_item:
            self.removeItem(self._preview_item)
            self._preview_item = None
        if self._preview_line:
            self.removeItem(self._preview_line)
            self._preview_line = None

    # --- Collision detection ---

    def check_collisions(self):
        from PySide6.QtGui import QPainterPath

        region_items = [item for item in self.items() if isinstance(item, RegionItem)]
        obstacles = [item for item in self.items() if isinstance(item, ObstacleItem)]
        walls = [item for item in self.items() if isinstance(item, WallItem)]

        for region in region_items:
            colliding = False
            for obs in obstacles:
                if region.collidesWithItem(obs):
                    colliding = True
                    break
            if not colliding:
                for other in region_items:
                    if other is not region and region.collidesWithItem(other):
                        colliding = True
                        break
            if not colliding and walls:
                for wall in walls:
                    wall_path = QPainterPath()
                    wall_path.addPolygon(wall.polygon())
                    wall_path.closeSubpath()
                    region_scene_path = region.mapToScene(region._boundary_item.shape())
                    region_path = QPainterPath()
                    region_path.addPolygon(region_scene_path)
                    if not wall_path.contains(region_path):
                        colliding = True
                        break
            region.set_collision(colliding)

    # --- Region loading ---

    def load_regions(self, regions: list[Region]) -> list[RegionItem]:
        """Add Region items to scene, stacked at center."""
        center = self.sceneRect().center()
        items = []
        for i, region in enumerate(regions):
            item = RegionItem(region, color_index=i)
            item.setPos(center.x(), center.y())
            self.addItem(item)
            items.append(item)
        return items

    # --- Background drawing ---

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        super().drawBackground(painter, rect)

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
        self.scale(50, 50)

    def wheelEvent(self, event: QWheelEvent) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            self.scene().handle_left_click(scene_pos)
            super().mousePressEvent(event)
        elif event.button() == Qt.MouseButton.RightButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            self.scene().handle_right_click(scene_pos)
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            self.scene().handle_double_click(scene_pos)
        else:
            super().mouseDoubleClickEvent(event)

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
            scene_pos = self.mapToScene(event.position().toPoint())
            self.scene().handle_mouse_move(scene_pos)
            super().mouseMoveEvent(event)
        scene_pos = self.mapToScene(event.position().toPoint())
        self.mouse_moved.emit(scene_pos.x(), scene_pos.y())
