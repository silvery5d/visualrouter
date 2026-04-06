from __future__ import annotations
import math
from PySide6.QtWidgets import (
    QGraphicsItemGroup, QGraphicsPolygonItem, QGraphicsEllipseItem,
    QGraphicsRectItem, QGraphicsItem, QGraphicsSimpleTextItem, QMenu,
    QGraphicsPathItem,
)
from PySide6.QtGui import QPen, QBrush, QColor, QPolygonF, QFont, QTransform, QPainterPath
from PySide6.QtCore import QPointF, Qt

from src.models.region import Region, VEHICLE_SIZE


REGION_COLORS = [
    QColor(255, 80, 80, 80),    # red
    QColor(80, 80, 255, 80),    # blue
    QColor(80, 200, 80, 80),    # green
    QColor(180, 80, 255, 80),   # purple
    QColor(255, 160, 40, 80),   # orange
    QColor(255, 255, 80, 80),   # yellow
    QColor(80, 220, 220, 80),   # cyan
]


class RegionItem(QGraphicsItemGroup):
    def __init__(self, region: Region, color_index: int = 0, parent=None):
        super().__init__(parent)
        self.region = region
        self._color = REGION_COLORS[color_index % len(REGION_COLORS)]
        self._collision = False
        self._rotating = False
        self._rotate_start_angle = 0.0
        self._rotate_start_mouse_angle = 0.0

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self._build_children()

        cx, cy = region.centroid()
        self.setTransformOriginPoint(QPointF(cx, cy))

    def _build_children(self):
        region = self.region

        # Boundary polygon
        pts = [QPointF(p.x, p.y) for p in region.boundary]
        self._boundary_item = QGraphicsPolygonItem(QPolygonF(pts))
        if region.category == "free_walk":
            pen = QPen(self._color.darker(150), 0.06, Qt.PenStyle.DashLine)
            self._boundary_item.setPen(pen)
        else:
            self._boundary_item.setPen(QPen(self._color.darker(150), 0.05))
        self._boundary_item.setBrush(QBrush(self._color))
        self.addToGroup(self._boundary_item)

        # StartPoint marker (green circle)
        sp = region.start_point.position
        r = 0.15
        self._start_marker = QGraphicsEllipseItem(sp.x - r, sp.y - r, r * 2, r * 2)
        self._start_marker.setBrush(QBrush(QColor(0, 200, 0, 180)))
        self._start_marker.setPen(QPen(Qt.PenStyle.NoPen))
        self.addToGroup(self._start_marker)

        # TargetArea marker (orange rect, centered on position)
        ta = region.target_area
        self._target_rect = QGraphicsRectItem(
            ta.position.x - ta.size.x / 2, ta.position.y - ta.size.y / 2, ta.size.x, ta.size.y
        )
        self._target_rect.setBrush(QBrush(QColor(255, 165, 0, 120)))
        self._target_rect.setPen(QPen(QColor(255, 140, 0), 0.03))
        self.addToGroup(self._target_rect)

        # Vehicle marker (blue rect + direction arrow)
        if region.has_vehicle and region.vehicle:
            vp = region.vehicle.relative_position
            vw, vh = VEHICLE_SIZE.x, VEHICLE_SIZE.y
            self._vehicle_rect = QGraphicsRectItem(
                vp.x - vw / 2, vp.y - vh / 2, vw, vh
            )
            self._vehicle_rect.setBrush(QBrush(QColor(50, 100, 255, 100)))
            self._vehicle_rect.setPen(QPen(QColor(30, 60, 200), 0.03))
            self.addToGroup(self._vehicle_rect)

            # Direction arrow (0° = up/+Y, clockwise)
            arrow_len = min(vw, vh) * 0.4
            angle_rad = math.radians(region.vehicle.angle)
            # 0° = +Y, 90° = +X (clockwise from up)
            dx = arrow_len * math.sin(angle_rad)
            dy = arrow_len * math.cos(angle_rad)
            ax, ay = vp.x, vp.y  # arrow center

            arrow_path = QPainterPath()
            arrow_path.moveTo(ax, ay)
            arrow_path.lineTo(ax + dx, ay + dy)
            # Arrowhead
            head_size = arrow_len * 0.35
            left_angle = angle_rad + math.radians(150)
            right_angle = angle_rad - math.radians(150)
            tip_x, tip_y = ax + dx, ay + dy
            arrow_path.moveTo(tip_x, tip_y)
            arrow_path.lineTo(
                tip_x + head_size * math.sin(left_angle),
                tip_y + head_size * math.cos(left_angle),
            )
            arrow_path.moveTo(tip_x, tip_y)
            arrow_path.lineTo(
                tip_x + head_size * math.sin(right_angle),
                tip_y + head_size * math.cos(right_angle),
            )
            arrow_item = QGraphicsPathItem(arrow_path)
            arrow_item.setPen(QPen(QColor(30, 60, 200), 0.06))
            self.addToGroup(arrow_item)

        # Name label with order number (flipped back since view Y is inverted)
        label_text = f"{region.order}. {region.name}" if region.order > 0 else region.name
        label = QGraphicsSimpleTextItem(label_text)
        label.setBrush(QBrush(self._color.darker(200)))
        font = QFont()
        font.setPointSize(12)
        label.setFont(font)
        label.setTransform(QTransform.fromScale(0.02, -0.02))  # scale to scene units + flip upright
        cx, cy = region.centroid()
        label.setPos(cx - 0.5, cy + 0.2)
        self.addToGroup(label)

    def rebuild(self):
        """Remove and recreate all child items to reflect model changes."""
        for child in self.childItems():
            self.removeFromGroup(child)
            if child.scene():
                child.scene().removeItem(child)
        self._build_children()
        cx, cy = self.region.centroid()
        self.setTransformOriginPoint(QPointF(cx, cy))

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            grid = self.scene().grid_size
            if self.scene()._snap_to_grid:
                x = round(value.x() / grid) * grid
                y = round(value.y() / grid) * grid
                value = QPointF(x, y)
            return value
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if self.scene():
                self.scene().region_moved.emit(self.region.name)
                self.scene().check_collisions()
        return super().itemChange(change, value)

    def set_collision(self, colliding: bool) -> None:
        if colliding != self._collision:
            self._collision = colliding
            pen_color = QColor(255, 0, 0) if colliding else self._color.darker(150)
            self._boundary_item.setPen(QPen(pen_color, 0.08 if colliding else 0.05))

    def get_canvas_start_point(self) -> tuple[float, float]:
        sp = self.region.start_point.position
        scene_pt = self.mapToScene(QPointF(sp.x, sp.y))
        return (scene_pt.x(), scene_pt.y())

    def get_placement_dict(self) -> dict:
        return {
            "region_name": self.region.name,
            "canvas_x": self.pos().x(),
            "canvas_y": self.pos().y(),
            "rotation": self.rotation(),
        }

    # --- Rotation via Shift+drag ---

    def mousePressEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self._rotating = True
            self._rotate_start_angle = self.rotation()
            center = self.transformOriginPoint()
            scene_center = self.mapToScene(center)
            scene_mouse = event.scenePos()
            self._rotate_start_mouse_angle = math.degrees(
                math.atan2(scene_mouse.y() - scene_center.y(), scene_mouse.x() - scene_center.x())
            )
        else:
            self._rotating = False
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._rotating:
            center = self.transformOriginPoint()
            scene_center = self.mapToScene(center)
            scene_mouse = event.scenePos()
            current_angle = math.degrees(
                math.atan2(scene_mouse.y() - scene_center.y(), scene_mouse.x() - scene_center.x())
            )
            delta = current_angle - self._rotate_start_mouse_angle
            self.setRotation(self._rotate_start_angle + delta)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._rotating = False
        super().mouseReleaseEvent(event)

    # --- Context menu ---

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = menu.addAction("删除")
        props_action = menu.addAction("属性")
        action = menu.exec(event.screenPos())
        if action == delete_action:
            self.scene().region_deleted.emit(self)
            self.scene().removeItem(self)
        elif action == props_action:
            self.setSelected(True)
