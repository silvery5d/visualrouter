from __future__ import annotations
from PySide6.QtWidgets import QGraphicsPolygonItem, QGraphicsItem, QMenu
from PySide6.QtGui import QPen, QBrush, QColor, QPolygonF
from PySide6.QtCore import QPointF, Qt


class WallItem(QGraphicsPolygonItem):
    def __init__(self, points: list[QPointF] | None = None, parent=None):
        super().__init__(parent)
        self.setPen(QPen(QColor(0, 0, 0), 0.05))
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        if points:
            self.setPolygon(QPolygonF(points))

    def set_points(self, points: list[QPointF]) -> None:
        self.setPolygon(QPolygonF(points))

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = menu.addAction("删除")
        action = menu.exec(event.screenPos())
        if action == delete_action:
            self.scene().removeItem(self)
