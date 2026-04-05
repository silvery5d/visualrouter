from __future__ import annotations
import os
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStatusBar, QSplitter, QFileDialog, QMessageBox,
)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QUndoStack, QUndoCommand
from src.graphics.canvas import VenueGraphicsScene, VenueGraphicsView
from src.graphics.region_item import RegionItem
from src.graphics.wall_item import WallItem
from src.graphics.obstacle_item import ObstacleItem
from src.widgets.toolbar import EditorToolBar
from src.widgets.side_panel import SidePanel
from src.models.project import Project, RegionPlacement
from src.models.region import Region
from src.models.venue import Wall, Obstacle, Point
from src.export.exporter import export_to_file
from src.widgets.toolbar import ToolMode


class MoveRegionCommand(QUndoCommand):
    def __init__(self, item: RegionItem, old_pos: QPointF, new_pos: QPointF):
        super().__init__(f"Move {item.region.name}")
        self.item = item
        self.old_pos = old_pos
        self.new_pos = new_pos

    def redo(self):
        self.item.setPos(self.new_pos)

    def undo(self):
        self.item.setPos(self.old_pos)


class RotateRegionCommand(QUndoCommand):
    def __init__(self, item: RegionItem, old_angle: float, new_angle: float):
        super().__init__(f"Rotate {item.region.name}")
        self.item = item
        self.old_angle = old_angle
        self.new_angle = new_angle

    def redo(self):
        self.item.setRotation(self.new_angle)

    def undo(self):
        self.item.setRotation(self.old_angle)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VisualRouter - VR场馆路线规划")
        self.setMinimumSize(1200, 800)

        self._project = Project()
        self._region_items: list[RegionItem] = []
        self._current_path: str | None = None
        self._undo_stack = QUndoStack(self)

        self.scene = VenueGraphicsScene()
        self.view = VenueGraphicsView(self.scene)

        self.side_panel = SidePanel()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.side_panel)
        splitter.addWidget(self.view)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        self.toolbar = EditorToolBar()
        self.addToolBar(self.toolbar)
        self.toolbar.mode_changed.connect(self.scene.set_tool_mode)
        self.toolbar.snap_toggled.connect(self._on_snap_toggled)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.view.mouse_moved.connect(self._update_mouse_pos)

        self.scene.region_moved.connect(self._on_region_moved)
        self.side_panel.region_selected.connect(self._on_side_panel_region_selected)

        self._create_menus()

    def _create_menus(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("文件")
        file_menu.addAction("新建项目", self._new_project, "Ctrl+N")
        file_menu.addAction("打开项目...", self._open_project, "Ctrl+O")
        file_menu.addAction("保存项目", self._save_project, "Ctrl+S")
        file_menu.addAction("另存为...", self._save_project_as, "Ctrl+Shift+S")
        file_menu.addSeparator()
        file_menu.addAction("导入VR配置...", self._import_vr_config)
        file_menu.addAction("导入背景图片...", self._import_background)
        file_menu.addSeparator()
        file_menu.addAction("导出配置JSON...", self._export_json)

        edit_menu = menu_bar.addMenu("编辑")
        edit_menu.addAction("撤销", self._undo, "Ctrl+Z")
        edit_menu.addAction("重做", self._redo, "Ctrl+Y")
        edit_menu.addSeparator()
        edit_menu.addAction("删除选中", self._delete_selected, "Delete")

        help_menu = menu_bar.addMenu("帮助")
        help_menu.addAction("快捷键", self._show_shortcuts)

    # --- Slots ---

    def set_region_items(self, items: list[RegionItem]) -> None:
        self._region_items = items
        self.side_panel.set_region_items(items)

    def _update_mouse_pos(self, x: float, y: float):
        self.status_bar.showMessage(f"X: {x:.2f}m  Y: {y:.2f}m")

    def _on_region_moved(self, name: str):
        for item in self._region_items:
            if item.region.name == name and item.isSelected():
                self.side_panel.update_properties(item)

    def _on_side_panel_region_selected(self, name: str):
        for item in self._region_items:
            item.setSelected(item.region.name == name)

    def _on_snap_toggled(self, enabled: bool):
        self.scene._snap_to_grid = enabled

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_S and not event.modifiers():
            self.toolbar.set_mode(ToolMode.SELECT)
        elif key == Qt.Key.Key_W and not event.modifiers():
            self.toolbar.set_mode(ToolMode.WALL)
        elif key == Qt.Key.Key_O and not event.modifiers():
            self.toolbar.set_mode(ToolMode.OBSTACLE)
        elif key == Qt.Key.Key_G and not event.modifiers():
            self.toolbar.toggle_snap()
        elif key == Qt.Key.Key_Escape:
            self.scene._cancel_drawing()
        else:
            super().keyPressEvent(event)

    # --- File operations ---

    def _new_project(self):
        self._project = Project()
        self.scene.clear()
        self._region_items = []
        self._current_path = None
        self.side_panel.set_region_items([])
        self.setWindowTitle("VisualRouter - 新建项目")

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开项目", "", "VR Project (*.vrproject)")
        if path:
            self._project = Project.load(path)
            self._current_path = path
            self._load_project_to_scene()
            self.setWindowTitle(f"VisualRouter - {os.path.basename(path)}")

    def _save_project(self):
        if self._current_path:
            self._collect_state_to_project()
            self._project.save(self._current_path)
        else:
            self._save_project_as()

    def _save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存项目", "", "VR Project (*.vrproject)")
        if path:
            self._current_path = path
            self._collect_state_to_project()
            self._project.save(path)
            self.setWindowTitle(f"VisualRouter - {os.path.basename(path)}")

    def _import_vr_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入VR配置", "", "JSON (*.json)")
        if path:
            regions = Region.load_from_file(path)
            self._region_items = self.scene.load_regions(regions)
            self.side_panel.set_region_items(self._region_items)
            self._project.vr_config_path = path

    def _import_background(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入背景图片", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.scene.set_background_image(path)
            if self._current_path:
                project_dir = os.path.dirname(self._current_path)
                self._project.venue.background_image = os.path.relpath(path, project_dir)
            else:
                self._project.venue.background_image = path

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出配置", "", "JSON (*.json)")
        if path:
            placements = [item.get_placement_dict() for item in self._region_items]
            regions = [item.region for item in self._region_items]
            export_to_file(regions, placements, path)

    # --- State management ---

    def _collect_state_to_project(self):
        # Collect walls
        self._project.venue.walls = []
        for item in self.scene.items():
            if isinstance(item, WallItem):
                polygon = item.polygon()
                points = [Point(polygon.at(i).x(), polygon.at(i).y()) for i in range(polygon.count())]
                self._project.venue.walls.append(Wall(points=points))

        # Collect obstacles
        self._project.venue.obstacles = []
        for item in self.scene.items():
            if isinstance(item, ObstacleItem):
                polygon = item.polygon()
                points = [Point(polygon.at(i).x(), polygon.at(i).y()) for i in range(polygon.count())]
                self._project.venue.obstacles.append(
                    Obstacle(name=getattr(item, 'obstacle_name', '障碍物'), type="polygon", points=points)
                )

        # Collect region placements
        self._project.region_placements = [
            RegionPlacement(
                region_name=item.region.name,
                canvas_x=item.pos().x(),
                canvas_y=item.pos().y(),
                rotation=item.rotation(),
            )
            for item in self._region_items
        ]

    def _load_project_to_scene(self):
        self.scene.clear()
        self._region_items = []

        # Restore background image
        if self._project.venue.background_image:
            bg_path = self._project.venue.background_image
            if self._current_path and not os.path.isabs(bg_path):
                bg_path = os.path.join(os.path.dirname(self._current_path), bg_path)
            if os.path.exists(bg_path):
                self.scene.set_background_image(bg_path)

        # Restore walls
        for wall in self._project.venue.walls:
            points = [QPointF(p.x, p.y) for p in wall.points]
            item = WallItem(points)
            self.scene.addItem(item)

        # Restore obstacles
        for obs in self._project.venue.obstacles:
            points = [QPointF(p.x, p.y) for p in obs.points]
            item = ObstacleItem(points)
            item.obstacle_name = obs.name
            self.scene.addItem(item)

        # Restore regions from VR config + placements
        if self._project.vr_config_path:
            vr_path = self._project.vr_config_path
            if self._current_path and not os.path.isabs(vr_path):
                vr_path = os.path.join(os.path.dirname(self._current_path), vr_path)
            if os.path.exists(vr_path):
                regions = Region.load_from_file(vr_path)
                self._region_items = self.scene.load_regions(regions)
                placement_map = {p.region_name: p for p in self._project.region_placements}
                for item in self._region_items:
                    pl = placement_map.get(item.region.name)
                    if pl:
                        item.setPos(pl.canvas_x, pl.canvas_y)
                        item.setRotation(pl.rotation)
                self.side_panel.set_region_items(self._region_items)

    # --- Edit operations ---

    def _undo(self):
        self._undo_stack.undo()

    def _redo(self):
        self._undo_stack.redo()

    def _delete_selected(self):
        for item in self.scene.selectedItems():
            self.scene.removeItem(item)
            if item in self._region_items:
                self._region_items.remove(item)

    def _show_shortcuts(self):
        QMessageBox.information(self, "快捷键", (
            "S: 选择模式\n"
            "W: 画墙壁模式\n"
            "O: 画障碍物模式\n"
            "G: 切换吸附网格\n"
            "Delete: 删除选中\n"
            "Ctrl+Z: 撤销\n"
            "Ctrl+Y: 重做\n"
            "Ctrl+N/O/S: 新建/打开/保存\n"
            "Escape: 取消当前绘制\n\n"
            "鼠标中键: 平移画布\n"
            "滚轮: 缩放\n"
            "Shift+拖拽: 旋转Region\n"
            "双击: 完成多边形绘制\n"
            "右键: 取消绘制 / 上下文菜单"
        ))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
