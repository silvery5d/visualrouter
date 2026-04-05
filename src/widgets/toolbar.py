from __future__ import annotations
from enum import Enum, auto
from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal


class ToolMode(Enum):
    SELECT = auto()
    WALL = auto()
    OBSTACLE = auto()


class EditorToolBar(QToolBar):
    mode_changed = Signal(ToolMode)
    snap_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__("Tools", parent)
        self._actions = {}
        self._current_mode = ToolMode.SELECT

        for mode, label in [
            (ToolMode.SELECT, "选择 (S)"),
            (ToolMode.WALL, "画墙壁 (W)"),
            (ToolMode.OBSTACLE, "画障碍物 (O)"),
        ]:
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, m=mode: self._set_mode(m))
            self.addAction(action)
            self._actions[mode] = action

        self._actions[ToolMode.SELECT].setChecked(True)

        self.addSeparator()
        self._snap_action = QAction("吸附网格 (G)", self)
        self._snap_action.setCheckable(True)
        self._snap_action.setChecked(True)
        self._snap_action.triggered.connect(self._on_snap_toggled)
        self.addAction(self._snap_action)

    def _on_snap_toggled(self, checked: bool) -> None:
        self.snap_toggled.emit(checked)

    def set_mode(self, mode: ToolMode) -> None:
        self._set_mode(mode)

    def toggle_snap(self) -> None:
        self._snap_action.setChecked(not self._snap_action.isChecked())
        self.snap_toggled.emit(self._snap_action.isChecked())

    def _set_mode(self, mode: ToolMode) -> None:
        self._current_mode = mode
        for m, action in self._actions.items():
            action.setChecked(m == mode)
        self.mode_changed.emit(mode)

    @property
    def current_mode(self) -> ToolMode:
        return self._current_mode
