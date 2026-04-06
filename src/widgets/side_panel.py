from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QGroupBox,
    QFormLayout, QDoubleSpinBox, QLabel, QListWidgetItem, QPushButton,
    QStackedWidget, QLineEdit, QComboBox, QSpinBox, QCheckBox,
)
from PySide6.QtCore import Signal, Qt

from src.graphics.region_item import RegionItem


class SidePanel(QWidget):
    region_selected = Signal(str)       # region name
    order_changed = Signal()
    edit_region_requested = Signal(str)  # region name - double click
    finish_edit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        layout = QVBoxLayout(self)

        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        # --- Page 0: Normal mode ---
        self._normal_page = QWidget()
        normal_layout = QVBoxLayout(self._normal_page)

        # Region list
        region_group = QGroupBox("Region 列表")
        region_layout = QVBoxLayout(region_group)
        self.region_list = QListWidget()
        self.region_list.currentItemChanged.connect(self._on_region_selected)
        self.region_list.itemDoubleClicked.connect(self._on_region_double_clicked)
        region_layout.addWidget(self.region_list)

        # Order buttons
        order_layout = QHBoxLayout()
        self._btn_up = QPushButton("▲ 上移")
        self._btn_down = QPushButton("▼ 下移")
        self._btn_up.clicked.connect(self._move_up)
        self._btn_down.clicked.connect(self._move_down)
        order_layout.addWidget(self._btn_up)
        order_layout.addWidget(self._btn_down)
        region_layout.addLayout(order_layout)
        normal_layout.addWidget(region_group)

        # Placement properties
        prop_group = QGroupBox("位置")
        prop_layout = QFormLayout(prop_group)

        self.pos_x_spin = QDoubleSpinBox()
        self.pos_x_spin.setRange(-1000, 1000)
        self.pos_x_spin.setDecimals(2)
        self.pos_x_spin.setSuffix(" m")
        prop_layout.addRow("X:", self.pos_x_spin)

        self.pos_y_spin = QDoubleSpinBox()
        self.pos_y_spin.setRange(-1000, 1000)
        self.pos_y_spin.setDecimals(2)
        self.pos_y_spin.setSuffix(" m")
        prop_layout.addRow("Y:", self.pos_y_spin)

        self.rotation_spin = QDoubleSpinBox()
        self.rotation_spin.setRange(-360, 360)
        self.rotation_spin.setDecimals(1)
        self.rotation_spin.setSuffix(" °")
        prop_layout.addRow("旋转:", self.rotation_spin)

        self.name_label = QLabel("-")
        prop_layout.addRow("名称:", self.name_label)

        normal_layout.addWidget(prop_group)
        normal_layout.addStretch()

        self._stack.addWidget(self._normal_page)

        # --- Page 1: Edit mode ---
        self._edit_page = QWidget()
        edit_layout = QVBoxLayout(self._edit_page)

        self._edit_title = QLabel()
        self._edit_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        edit_layout.addWidget(self._edit_title)

        # Basic info
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)

        self._edit_name = QLineEdit()
        basic_layout.addRow("名称:", self._edit_name)

        self._edit_category = QComboBox()
        self._edit_category.addItems(["normal", "free_walk"])
        basic_layout.addRow("类别:", self._edit_category)

        self._edit_order = QSpinBox()
        self._edit_order.setRange(0, 999)
        basic_layout.addRow("顺序:", self._edit_order)

        edit_layout.addWidget(basic_group)

        # StartPoint
        sp_group = QGroupBox("起始点 (StartPoint)")
        sp_layout = QFormLayout(sp_group)

        self._edit_sp_x = QDoubleSpinBox()
        self._edit_sp_x.setRange(-100, 100)
        self._edit_sp_x.setDecimals(2)
        self._edit_sp_x.setSuffix(" m")
        sp_layout.addRow("X:", self._edit_sp_x)

        self._edit_sp_y = QDoubleSpinBox()
        self._edit_sp_y.setRange(-100, 100)
        self._edit_sp_y.setDecimals(2)
        self._edit_sp_y.setSuffix(" m")
        sp_layout.addRow("Y:", self._edit_sp_y)

        self._edit_sp_angle = QDoubleSpinBox()
        self._edit_sp_angle.setRange(-360, 360)
        self._edit_sp_angle.setDecimals(1)
        self._edit_sp_angle.setSuffix(" °")
        sp_layout.addRow("角度:", self._edit_sp_angle)

        edit_layout.addWidget(sp_group)

        # TargetArea
        ta_group = QGroupBox("目标区域 (TargetArea)")
        ta_layout = QFormLayout(ta_group)

        self._edit_ta_x = QDoubleSpinBox()
        self._edit_ta_x.setRange(-100, 100)
        self._edit_ta_x.setDecimals(2)
        self._edit_ta_x.setSuffix(" m")
        ta_layout.addRow("X:", self._edit_ta_x)

        self._edit_ta_y = QDoubleSpinBox()
        self._edit_ta_y.setRange(-100, 100)
        self._edit_ta_y.setDecimals(2)
        self._edit_ta_y.setSuffix(" m")
        ta_layout.addRow("Y:", self._edit_ta_y)

        self._edit_ta_w = QDoubleSpinBox()
        self._edit_ta_w.setRange(0.1, 100)
        self._edit_ta_w.setDecimals(2)
        self._edit_ta_w.setSuffix(" m")
        ta_layout.addRow("宽:", self._edit_ta_w)

        self._edit_ta_h = QDoubleSpinBox()
        self._edit_ta_h.setRange(0.1, 100)
        self._edit_ta_h.setDecimals(2)
        self._edit_ta_h.setSuffix(" m")
        ta_layout.addRow("高:", self._edit_ta_h)

        edit_layout.addWidget(ta_group)

        # Vehicle
        veh_group = QGroupBox("载具 (Vehicle)")
        veh_layout = QFormLayout(veh_group)

        self._edit_has_vehicle = QCheckBox("启用载具")
        veh_layout.addRow(self._edit_has_vehicle)

        self._edit_veh_x = QDoubleSpinBox()
        self._edit_veh_x.setRange(-100, 100)
        self._edit_veh_x.setDecimals(2)
        self._edit_veh_x.setSuffix(" m")
        veh_layout.addRow("X:", self._edit_veh_x)

        self._edit_veh_y = QDoubleSpinBox()
        self._edit_veh_y.setRange(-100, 100)
        self._edit_veh_y.setDecimals(2)
        self._edit_veh_y.setSuffix(" m")
        veh_layout.addRow("Y:", self._edit_veh_y)

        self._edit_veh_angle = QDoubleSpinBox()
        self._edit_veh_angle.setRange(-360, 360)
        self._edit_veh_angle.setDecimals(1)
        self._edit_veh_angle.setSuffix(" °")
        veh_layout.addRow("角度:", self._edit_veh_angle)

        self._edit_has_vehicle.toggled.connect(self._on_vehicle_toggled)
        edit_layout.addWidget(veh_group)

        # Finish button
        self._btn_finish = QPushButton("完成编辑")
        self._btn_finish.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-size: 14px;")
        self._btn_finish.clicked.connect(self._on_finish_edit)
        edit_layout.addWidget(self._btn_finish)

        edit_layout.addStretch()
        self._stack.addWidget(self._edit_page)

        # State
        self._region_items: dict[str, RegionItem] = {}
        self._updating = False
        self._editing_region: RegionItem | None = None

        # Normal mode connections
        self.pos_x_spin.valueChanged.connect(self._on_pos_changed)
        self.pos_y_spin.valueChanged.connect(self._on_pos_changed)
        self.rotation_spin.valueChanged.connect(self._on_rotation_changed)

        # Edit mode connections
        self._edit_sp_x.valueChanged.connect(self._on_edit_changed)
        self._edit_sp_y.valueChanged.connect(self._on_edit_changed)
        self._edit_sp_angle.valueChanged.connect(self._on_edit_changed)
        self._edit_ta_x.valueChanged.connect(self._on_edit_changed)
        self._edit_ta_y.valueChanged.connect(self._on_edit_changed)
        self._edit_ta_w.valueChanged.connect(self._on_edit_changed)
        self._edit_ta_h.valueChanged.connect(self._on_edit_changed)
        self._edit_veh_x.valueChanged.connect(self._on_edit_changed)
        self._edit_veh_y.valueChanged.connect(self._on_edit_changed)
        self._edit_veh_angle.valueChanged.connect(self._on_edit_changed)
        self._edit_name.textChanged.connect(self._on_edit_changed)
        self._edit_category.currentTextChanged.connect(self._on_edit_changed)
        self._edit_order.valueChanged.connect(self._on_edit_changed)
        self._edit_has_vehicle.toggled.connect(self._on_edit_changed)

    # --- Normal mode ---

    def set_region_items(self, items: list[RegionItem]) -> None:
        self.region_list.clear()
        self._region_items.clear()
        sorted_items = sorted(items, key=lambda it: it.region.order)
        for item in sorted_items:
            r = item.region
            label = f"{r.order}. {r.name}" if r.order > 0 else r.name
            list_item = QListWidgetItem(label)
            list_item.setData(Qt.ItemDataRole.UserRole, r.name)
            self.region_list.addItem(list_item)
            self._region_items[r.name] = item

    def update_properties(self, region_item: RegionItem) -> None:
        self._updating = True
        self.name_label.setText(region_item.region.name)
        self.pos_x_spin.setValue(region_item.pos().x())
        self.pos_y_spin.setValue(region_item.pos().y())
        self.rotation_spin.setValue(region_item.rotation())
        self._updating = False

    def _on_region_selected(self, current, previous):
        if current:
            name = current.data(Qt.ItemDataRole.UserRole)
            self.region_selected.emit(name)
            if name in self._region_items:
                self.update_properties(self._region_items[name])

    def _on_region_double_clicked(self, item):
        name = item.data(Qt.ItemDataRole.UserRole)
        if name in self._region_items:
            self.edit_region_requested.emit(name)

    def _move_up(self):
        row = self.region_list.currentRow()
        if row <= 0:
            return
        self._swap_order(row, row - 1)

    def _move_down(self):
        row = self.region_list.currentRow()
        if row < 0 or row >= self.region_list.count() - 1:
            return
        self._swap_order(row, row + 1)

    def _swap_order(self, row_a, row_b):
        name_a = self.region_list.item(row_a).data(Qt.ItemDataRole.UserRole)
        name_b = self.region_list.item(row_b).data(Qt.ItemDataRole.UserRole)
        item_a = self._region_items[name_a]
        item_b = self._region_items[name_b]
        item_a.region.order, item_b.region.order = item_b.region.order, item_a.region.order
        items = list(self._region_items.values())
        self.set_region_items(items)
        for i in range(self.region_list.count()):
            if self.region_list.item(i).data(Qt.ItemDataRole.UserRole) == name_a:
                self.region_list.setCurrentRow(i)
                break
        self.order_changed.emit()

    def _on_pos_changed(self):
        if self._updating:
            return
        current = self.region_list.currentItem()
        if current:
            name = current.data(Qt.ItemDataRole.UserRole)
            if name in self._region_items:
                self._region_items[name].setPos(self.pos_x_spin.value(), self.pos_y_spin.value())

    def _on_rotation_changed(self):
        if self._updating:
            return
        current = self.region_list.currentItem()
        if current:
            name = current.data(Qt.ItemDataRole.UserRole)
            if name in self._region_items:
                self._region_items[name].setRotation(self.rotation_spin.value())

    # --- Edit mode ---

    def enter_edit_mode(self, region_item: RegionItem) -> None:
        self._editing_region = region_item
        self._load_edit_fields(region_item)
        self._stack.setCurrentIndex(1)

    def exit_edit_mode(self) -> None:
        self._editing_region = None
        self._stack.setCurrentIndex(0)

    def _load_edit_fields(self, region_item: RegionItem) -> None:
        self._updating = True
        r = region_item.region
        self._edit_title.setText(f"编辑: {r.name}")
        self._edit_name.setText(r.name)
        self._edit_category.setCurrentText(r.category)
        self._edit_order.setValue(r.order)

        sp = r.start_point
        self._edit_sp_x.setValue(sp.position.x)
        self._edit_sp_y.setValue(sp.position.y)
        self._edit_sp_angle.setValue(sp.angle)

        ta = r.target_area
        self._edit_ta_x.setValue(ta.position.x)
        self._edit_ta_y.setValue(ta.position.y)
        self._edit_ta_w.setValue(ta.size.x)
        self._edit_ta_h.setValue(ta.size.y)

        self._edit_has_vehicle.setChecked(r.has_vehicle)
        if r.has_vehicle and r.vehicle:
            self._edit_veh_x.setValue(r.vehicle.relative_position.x)
            self._edit_veh_y.setValue(r.vehicle.relative_position.y)
            self._edit_veh_angle.setValue(r.vehicle.angle)
        self._on_vehicle_toggled(r.has_vehicle)
        self._updating = False

    def _on_vehicle_toggled(self, checked):
        self._edit_veh_x.setEnabled(checked)
        self._edit_veh_y.setEnabled(checked)
        self._edit_veh_angle.setEnabled(checked)

    def _on_edit_changed(self):
        if self._updating or not self._editing_region:
            return
        self._apply_edit_to_region()

    def _apply_edit_to_region(self) -> None:
        r = self._editing_region.region
        r.name = self._edit_name.text()
        r.category = self._edit_category.currentText()
        r.order = self._edit_order.value()

        r.start_point.position.x = self._edit_sp_x.value()
        r.start_point.position.y = self._edit_sp_y.value()
        r.start_point.angle = self._edit_sp_angle.value()

        r.target_area.position.x = self._edit_ta_x.value()
        r.target_area.position.y = self._edit_ta_y.value()
        r.target_area.size.x = self._edit_ta_w.value()
        r.target_area.size.y = self._edit_ta_h.value()

        r.has_vehicle = self._edit_has_vehicle.isChecked()
        if r.has_vehicle:
            from src.models.region import Vehicle
            from src.models.venue import Point
            if not r.vehicle:
                r.vehicle = Vehicle(relative_position=Point(0, 0))
            r.vehicle.relative_position.x = self._edit_veh_x.value()
            r.vehicle.relative_position.y = self._edit_veh_y.value()
            r.vehicle.angle = self._edit_veh_angle.value()

        self._editing_region.rebuild()

    def update_edit_fields_from_region(self) -> None:
        """Called when canvas dragging changes marker positions."""
        if not self._editing_region:
            return
        self._load_edit_fields(self._editing_region)

    def _on_finish_edit(self):
        self.finish_edit_requested.emit()
