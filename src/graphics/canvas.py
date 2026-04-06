from __future__ import annotations
import math
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsLineItem
from PySide6.QtCore import Qt, QRectF, QPointF, QLineF, Signal
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
    region_deleted = Signal(object)      # emits RegionItem

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_size = 0.25  # meters
        self.setSceneRect(0, 0, 20, 15)  # 20m x 15m fixed
        self._background_pixmap = None

        self._tool_mode = ToolMode.SELECT
        self._snap_to_grid = True
        self._edit_mode = False
        self._drawing_points: list[QPointF] = []
        self._preview_item = None  # live polygon preview while drawing
        self._preview_line = None  # line from last point to cursor

        # Eraser state
        self._eraser_width = 0.5  # meters
        self._eraser_preview = None  # QGraphicsLineItem for red highlight
        self._eraser_target = None   # (WallItem, edge_idx, pt_start, pt_end)

    def set_tool_mode(self, mode: ToolMode) -> None:
        if self._tool_mode != mode:
            self._cancel_drawing()
            if self._eraser_preview:
                self.removeItem(self._eraser_preview)
                self._eraser_preview = None
            self._eraser_target = None
        self._tool_mode = mode

    def set_background_image(self, path: str) -> None:
        self._background_pixmap = QPixmap(path)
        self.update()

    def clear_background_image(self) -> None:
        self._background_pixmap = None
        self.update()

    # --- Drawing interaction ---

    def handle_left_click(self, scene_pos: QPointF) -> None:
        if self._edit_mode:
            # In edit mode, clicking empty space adds vertex on nearest edge
            # But only if not clicking on an existing handle
            item_at = self.itemAt(scene_pos, self.views()[0].transform() if self.views() else __import__('PySide6.QtGui', fromlist=['QTransform']).QTransform())
            if item_at is None:
                # No item under cursor - try to add vertex
                from src.graphics.region_editor import VertexHandle, MarkerHandle, TargetAreaHandle, ResizeHandle, VehicleHandle
                if hasattr(self, '_main_window') and self._main_window._region_editor:
                    self._main_window._region_editor.add_vertex_on_edge(scene_pos)
            return
        if self._tool_mode == ToolMode.ERASER:
            self._perform_erase()
            return
        if self._tool_mode in (ToolMode.WALL, ToolMode.OBSTACLE):
            self._add_drawing_point(scene_pos)

    def handle_double_click(self, scene_pos: QPointF) -> None:
        if self._tool_mode in (ToolMode.WALL, ToolMode.OBSTACLE):
            self._finish_drawing()

    def handle_right_click(self, scene_pos: QPointF) -> None:
        if self._tool_mode in (ToolMode.WALL, ToolMode.OBSTACLE):
            self._cancel_drawing()

    def handle_mouse_move(self, scene_pos: QPointF) -> None:
        if self._tool_mode == ToolMode.ERASER:
            self._update_eraser_preview(scene_pos)
            return
        if self._tool_mode in (ToolMode.WALL, ToolMode.OBSTACLE) and self._drawing_points:
            self._update_preview_line(scene_pos)

    def _snap(self, pos: QPointF) -> QPointF:
        if self._snap_to_grid:
            x = round(pos.x() / self.grid_size) * self.grid_size
            y = round(pos.y() / self.grid_size) * self.grid_size
            return QPointF(x, y)
        return pos

    def _add_drawing_point(self, pos: QPointF) -> None:
        self._drawing_points.append(self._snap(pos))
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

    # --- Eraser ---

    def _update_eraser_preview(self, cursor: QPointF) -> None:
        # Clear old preview
        if self._eraser_preview:
            self.removeItem(self._eraser_preview)
            self._eraser_preview = None
        self._eraser_target = None

        walls = [item for item in self.items() if isinstance(item, WallItem)]
        best_dist = float('inf')
        best_wall = None
        best_edge = -1
        best_proj = None

        for wall in walls:
            poly = wall.polygon()
            n = poly.count()
            for i in range(n):
                p1 = poly.at(i)
                p2 = poly.at((i + 1) % n)
                proj, dist = self._point_to_segment(cursor, p1, p2)
                if dist < best_dist:
                    best_dist = dist
                    best_wall = wall
                    best_edge = i
                    best_proj = proj

        # Only show preview if close enough (within 0.5m of an edge)
        if best_dist > 0.5 or best_wall is None:
            return

        poly = best_wall.polygon()
        p1 = poly.at(best_edge)
        p2 = poly.at((best_edge + 1) % poly.count())
        edge_dx = p2.x() - p1.x()
        edge_dy = p2.y() - p1.y()
        edge_len = math.hypot(edge_dx, edge_dy)
        if edge_len < 0.01:
            return

        # Parameter t of projection on edge
        t_proj = ((best_proj.x() - p1.x()) * edge_dx + (best_proj.y() - p1.y()) * edge_dy) / (edge_len * edge_len)
        half_w = (self._eraser_width / 2) / edge_len
        t_start = max(0.0, t_proj - half_w)
        t_end = min(1.0, t_proj + half_w)

        pt_start = QPointF(p1.x() + t_start * edge_dx, p1.y() + t_start * edge_dy)
        pt_end = QPointF(p1.x() + t_end * edge_dx, p1.y() + t_end * edge_dy)

        self._eraser_preview = QGraphicsLineItem(QLineF(pt_start, pt_end))
        self._eraser_preview.setPen(QPen(QColor(255, 0, 0, 180), 0.1))
        self.addItem(self._eraser_preview)
        self._eraser_target = (best_wall, best_edge, t_start, t_end)

    def _perform_erase(self) -> None:
        if not self._eraser_target:
            return
        wall, edge_idx, t_start, t_end = self._eraser_target

        poly = wall.polygon()
        n = poly.count()
        p1 = poly.at(edge_idx)
        p2 = poly.at((edge_idx + 1) % n)
        edge_dx = p2.x() - p1.x()
        edge_dy = p2.y() - p1.y()

        pt_start = QPointF(p1.x() + t_start * edge_dx, p1.y() + t_start * edge_dy)
        pt_end = QPointF(p1.x() + t_end * edge_dx, p1.y() + t_end * edge_dy)

        # Build the remaining points as an open polyline
        # Walk from pt_end -> around the polygon -> pt_start (skipping the erased gap)
        remaining = []

        # If we're erasing the full edge, skip both endpoints
        if t_end < 1.0:
            remaining.append(pt_end)

        # Continue from next vertex around the polygon
        for k in range(1, n):
            idx = (edge_idx + 1 + k) % n
            remaining.append(QPointF(poly.at(idx).x(), poly.at(idx).y()))

        if t_start > 0.0:
            remaining.append(pt_start)

        # Remove old wall and preview
        self.removeItem(wall)
        if self._eraser_preview:
            self.removeItem(self._eraser_preview)
            self._eraser_preview = None
        self._eraser_target = None

        # Create new wall from remaining points (if enough points)
        if len(remaining) >= 2:
            new_wall = WallItem(remaining)
            self.addItem(new_wall)

    @staticmethod
    def _point_to_segment(p: QPointF, a: QPointF, b: QPointF) -> tuple[QPointF, float]:
        """Project point p onto segment ab. Returns (projection_point, distance)."""
        dx, dy = b.x() - a.x(), b.y() - a.y()
        len_sq = dx * dx + dy * dy
        if len_sq < 1e-10:
            return a, math.hypot(p.x() - a.x(), p.y() - a.y())
        t = max(0.0, min(1.0, ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / len_sq))
        proj = QPointF(a.x() + t * dx, a.y() + t * dy)
        dist = math.hypot(p.x() - proj.x(), p.y() - proj.y())
        return proj, dist

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
        minor_pen = QPen(QColor(220, 220, 220), 0)
        major_pen = QPen(QColor(80, 80, 80), 0)

        import math
        left = math.floor(rect.left() / self.grid_size) * self.grid_size
        top = math.floor(rect.top() / self.grid_size) * self.grid_size

        x = left
        while x <= rect.right():
            is_major = abs(round(x / self.grid_size) % 4) == 0
            painter.setPen(major_pen if is_major else minor_pen)
            painter.drawLine(QLineF(x, rect.top(), x, rect.bottom()))
            x += self.grid_size

        y = top
        while y <= rect.bottom():
            is_major = abs(round(y / self.grid_size) % 4) == 0
            painter.setPen(major_pen if is_major else minor_pen)
            painter.drawLine(QLineF(rect.left(), y, rect.right(), y))
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

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._fit_to_scene()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._fit_to_scene()

    def _fit_to_scene(self) -> None:
        self.resetTransform()
        self.scale(1, -1)  # flip Y: (0,0) bottom-left, Y up
        self.fitInView(self.scene().sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event: QWheelEvent) -> None:
        event.ignore()  # disable zoom

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
        scene_rect = self.scene().sceneRect()
        user_y = scene_rect.height() - scene_pos.y()
        self.mouse_moved.emit(scene_pos.x(), user_y)
