"""Handles region editing: vertex control points, draggable markers."""
from __future__ import annotations
import math
from PySide6.QtWidgets import (
    QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsItem,
    QGraphicsPolygonItem, QGraphicsLineItem, QMenu,
)
from PySide6.QtGui import QPen, QBrush, QColor, QPolygonF
from PySide6.QtCore import QPointF, Qt, QRectF

from src.models.region import Region, VEHICLE_SIZE


HANDLE_SIZE = 0.15  # meters


class VertexHandle(QGraphicsEllipseItem):
    """Draggable handle for a boundary vertex."""
    def __init__(self, index: int, pos: QPointF, editor: RegionEditor):
        r = HANDLE_SIZE
        super().__init__(-r, -r, r * 2, r * 2)
        self.setPos(pos)
        self.index = index
        self._editor = editor
        self.setBrush(QBrush(QColor(255, 255, 255)))
        self.setPen(QPen(QColor(0, 0, 0), 0.03))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(10)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            grid = self.scene().grid_size
            if self.scene()._snap_to_grid:
                x = round(value.x() / grid) * grid
                y = round(value.y() / grid) * grid
                value = QPointF(x, y)
            return value
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._editor.on_vertex_moved(self.index, self.pos())
        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        if len(self._editor._region.boundary) <= 3:
            return
        menu = QMenu()
        delete_action = menu.addAction("删除顶点")
        action = menu.exec(event.screenPos())
        if action == delete_action:
            self._editor.delete_vertex(self.index)


class MarkerHandle(QGraphicsEllipseItem):
    """Draggable handle for StartPoint."""
    def __init__(self, pos: QPointF, color: QColor, editor: RegionEditor, marker_type: str):
        r = 0.2
        super().__init__(-r, -r, r * 2, r * 2)
        self.setPos(pos)
        self._editor = editor
        self._marker_type = marker_type
        self.setBrush(QBrush(color))
        self.setPen(QPen(color.darker(150), 0.03))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(10)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            grid = self.scene().grid_size
            if self.scene()._snap_to_grid:
                x = round(value.x() / grid) * grid
                y = round(value.y() / grid) * grid
                value = QPointF(x, y)
            return value
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._editor.on_marker_moved(self._marker_type, self.pos())
        return super().itemChange(change, value)


class TargetAreaHandle(QGraphicsRectItem):
    """Draggable handle for TargetArea center."""
    def __init__(self, pos: QPointF, size_x: float, size_y: float, editor: RegionEditor):
        super().__init__(-size_x / 2, -size_y / 2, size_x, size_y)
        self.setPos(pos)
        self._editor = editor
        self.setBrush(QBrush(QColor(255, 165, 0, 120)))
        self.setPen(QPen(QColor(255, 140, 0), 0.03))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(10)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            grid = self.scene().grid_size
            if self.scene()._snap_to_grid:
                x = round(value.x() / grid) * grid
                y = round(value.y() / grid) * grid
                value = QPointF(x, y)
            return value
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._editor.on_marker_moved("target", self.pos())
        return super().itemChange(change, value)


class ResizeHandle(QGraphicsRectItem):
    """Corner handle for resizing TargetArea."""
    def __init__(self, corner: str, editor: RegionEditor):
        s = HANDLE_SIZE
        super().__init__(-s, -s, s * 2, s * 2)
        self._corner = corner  # "tl", "tr", "bl", "br"
        self._editor = editor
        self.setBrush(QBrush(QColor(255, 140, 0)))
        self.setPen(QPen(QColor(200, 100, 0), 0.02))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(11)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            grid = self.scene().grid_size
            if self.scene()._snap_to_grid:
                x = round(value.x() / grid) * grid
                y = round(value.y() / grid) * grid
                value = QPointF(x, y)
            return value
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._editor.on_resize_handle_moved(self._corner, self.pos())
        return super().itemChange(change, value)


class VehicleHandle(QGraphicsRectItem):
    """Draggable handle for Vehicle."""
    def __init__(self, pos: QPointF, editor: RegionEditor):
        vw, vh = VEHICLE_SIZE.x, VEHICLE_SIZE.y
        super().__init__(-vw / 2, -vh / 2, vw, vh)
        self.setPos(pos)
        self._editor = editor
        self.setBrush(QBrush(QColor(50, 100, 255, 100)))
        self.setPen(QPen(QColor(30, 60, 200), 0.03))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(10)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            grid = self.scene().grid_size
            if self.scene()._snap_to_grid:
                x = round(value.x() / grid) * grid
                y = round(value.y() / grid) * grid
                value = QPointF(x, y)
            return value
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._editor.on_marker_moved("vehicle", self.pos())
        return super().itemChange(change, value)


class RegionEditor:
    """Manages the edit-mode overlay for a single region."""
    def __init__(self, region: Region, scene, on_changed=None):
        self._region = region
        self._scene = scene
        self._on_changed = on_changed
        self._boundary_item = None
        self._vertex_handles: list[VertexHandle] = []
        self._edge_lines: list[QGraphicsLineItem] = []
        self._sp_handle = None
        self._ta_handle = None
        self._ta_resize_handles: list[ResizeHandle] = []
        self._veh_handle = None
        self._items: list[QGraphicsItem] = []

    def setup(self) -> None:
        self._draw_boundary()
        self._draw_start_point()
        self._draw_target_area()
        if self._region.has_vehicle and self._region.vehicle:
            self._draw_vehicle()

    def cleanup(self) -> None:
        for item in self._items:
            if item.scene():
                self._scene.removeItem(item)
        self._items.clear()
        self._vertex_handles.clear()
        self._edge_lines.clear()
        self._ta_resize_handles.clear()

    def _track(self, item):
        self._items.append(item)
        self._scene.addItem(item)
        return item

    def _draw_boundary(self) -> None:
        pts = [QPointF(p.x, p.y) for p in self._region.boundary]
        self._boundary_item = QGraphicsPolygonItem(QPolygonF(pts))
        self._boundary_item.setPen(QPen(QColor(100, 100, 255), 0.04))
        self._boundary_item.setBrush(QBrush(QColor(100, 100, 255, 30)))
        self._boundary_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self._track(self._boundary_item)

        for i, p in enumerate(self._region.boundary):
            handle = VertexHandle(i, QPointF(p.x, p.y), self)
            self._vertex_handles.append(handle)
            self._track(handle)

    def _draw_start_point(self) -> None:
        sp = self._region.start_point.position
        self._sp_handle = MarkerHandle(
            QPointF(sp.x, sp.y), QColor(0, 200, 0, 180), self, "start"
        )
        self._track(self._sp_handle)

    def _draw_target_area(self) -> None:
        ta = self._region.target_area
        self._ta_handle = TargetAreaHandle(
            QPointF(ta.position.x, ta.position.y), ta.size.x, ta.size.y, self
        )
        self._track(self._ta_handle)

        # Resize handles at corners
        self._update_resize_handles()

    def _update_resize_handles(self) -> None:
        for h in self._ta_resize_handles:
            if h.scene():
                self._scene.removeItem(h)
            if h in self._items:
                self._items.remove(h)
        self._ta_resize_handles.clear()

        ta = self._region.target_area
        cx, cy = ta.position.x, ta.position.y
        hw, hh = ta.size.x / 2, ta.size.y / 2
        corners = {
            "tl": QPointF(cx - hw, cy + hh),
            "tr": QPointF(cx + hw, cy + hh),
            "bl": QPointF(cx - hw, cy - hh),
            "br": QPointF(cx + hw, cy - hh),
        }
        for name, pos in corners.items():
            handle = ResizeHandle(name, self)
            handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)
            handle.setPos(pos)
            handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
            self._ta_resize_handles.append(handle)
            self._track(handle)

    def _draw_vehicle(self) -> None:
        veh = self._region.vehicle
        self._veh_handle = VehicleHandle(
            QPointF(veh.relative_position.x, veh.relative_position.y), self
        )
        self._track(self._veh_handle)

    def on_vertex_moved(self, index: int, pos: QPointF) -> None:
        self._region.boundary[index].x = pos.x()
        self._region.boundary[index].y = pos.y()
        self._refresh_boundary()
        self._notify()

    def delete_vertex(self, index: int) -> None:
        if len(self._region.boundary) <= 3:
            return
        del self._region.boundary[index]
        self._full_refresh()
        self._notify()

    def add_vertex_on_edge(self, scene_pos: QPointF) -> None:
        """Find nearest edge and insert a new vertex."""
        best_dist = float('inf')
        best_idx = -1
        pts = self._region.boundary
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            p1 = QPointF(pts[i].x, pts[i].y)
            p2 = QPointF(pts[j].x, pts[j].y)
            proj, dist = self._point_to_segment(scene_pos, p1, p2)
            if dist < best_dist:
                best_dist = dist
                best_idx = j

        if best_dist < 0.5 and best_idx >= 0:
            from src.models.venue import Point
            snapped = scene_pos
            if self._scene._snap_to_grid:
                g = self._scene.grid_size
                snapped = QPointF(round(scene_pos.x() / g) * g, round(scene_pos.y() / g) * g)
            self._region.boundary.insert(best_idx, Point(snapped.x(), snapped.y()))
            self._full_refresh()
            self._notify()

    def on_marker_moved(self, marker_type: str, pos: QPointF) -> None:
        if marker_type == "start":
            self._region.start_point.position.x = pos.x()
            self._region.start_point.position.y = pos.y()
        elif marker_type == "target":
            self._region.target_area.position.x = pos.x()
            self._region.target_area.position.y = pos.y()
            self._update_resize_handles()
        elif marker_type == "vehicle" and self._region.vehicle:
            self._region.vehicle.relative_position.x = pos.x()
            self._region.vehicle.relative_position.y = pos.y()
        self._notify()

    def on_resize_handle_moved(self, corner: str, pos: QPointF) -> None:
        ta = self._region.target_area
        cx, cy = ta.position.x, ta.position.y

        if "l" in corner:
            new_hw = cx - pos.x()
        else:
            new_hw = pos.x() - cx
        if "b" in corner:
            new_hh = cy - pos.y()
        else:
            new_hh = pos.y() - cy

        ta.size.x = max(0.1, abs(new_hw) * 2)
        ta.size.y = max(0.1, abs(new_hh) * 2)

        # Refresh the TargetArea visual
        if self._ta_handle and self._ta_handle.scene():
            self._scene.removeItem(self._ta_handle)
            self._items.remove(self._ta_handle)
        self._ta_handle = TargetAreaHandle(
            QPointF(ta.position.x, ta.position.y), ta.size.x, ta.size.y, self
        )
        self._ta_handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)
        self._track(self._ta_handle)
        self._ta_handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self._update_resize_handles()
        self._notify()

    def _refresh_boundary(self) -> None:
        pts = [QPointF(p.x, p.y) for p in self._region.boundary]
        if self._boundary_item:
            self._boundary_item.setPolygon(QPolygonF(pts))

    def _full_refresh(self) -> None:
        self.cleanup()
        self.setup()

    def _notify(self) -> None:
        if self._on_changed:
            self._on_changed()

    @staticmethod
    def _point_to_segment(p: QPointF, a: QPointF, b: QPointF) -> tuple[QPointF, float]:
        dx, dy = b.x() - a.x(), b.y() - a.y()
        len_sq = dx * dx + dy * dy
        if len_sq < 1e-10:
            return a, math.hypot(p.x() - a.x(), p.y() - a.y())
        t = max(0.0, min(1.0, ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / len_sq))
        proj = QPointF(a.x() + t * dx, a.y() + t * dy)
        dist = math.hypot(p.x() - proj.x(), p.y() - proj.y())
        return proj, dist
