from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QGroupBox,
    QFormLayout, QDoubleSpinBox, QLabel, QListWidgetItem,
)
from PySide6.QtCore import Signal

from src.graphics.region_item import RegionItem


class SidePanel(QWidget):
    region_selected = Signal(str)  # region name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        layout = QVBoxLayout(self)

        # Region list
        region_group = QGroupBox("Region 列表")
        region_layout = QVBoxLayout(region_group)
        self.region_list = QListWidget()
        self.region_list.currentItemChanged.connect(self._on_region_selected)
        region_layout.addWidget(self.region_list)
        layout.addWidget(region_group)

        # Property editor
        prop_group = QGroupBox("属性")
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

        layout.addWidget(prop_group)
        layout.addStretch()

        self._region_items: dict[str, RegionItem] = {}
        self._updating = False

        self.pos_x_spin.valueChanged.connect(self._on_pos_changed)
        self.pos_y_spin.valueChanged.connect(self._on_pos_changed)
        self.rotation_spin.valueChanged.connect(self._on_rotation_changed)

    def set_region_items(self, items: list[RegionItem]) -> None:
        self.region_list.clear()
        self._region_items.clear()
        for item in items:
            list_item = QListWidgetItem(item.region.name)
            self.region_list.addItem(list_item)
            self._region_items[item.region.name] = item

    def update_properties(self, region_item: RegionItem) -> None:
        self._updating = True
        self.name_label.setText(region_item.region.name)
        self.pos_x_spin.setValue(region_item.pos().x())
        self.pos_y_spin.setValue(region_item.pos().y())
        self.rotation_spin.setValue(region_item.rotation())
        self._updating = False

    def _on_region_selected(self, current, previous):
        if current:
            name = current.text()
            self.region_selected.emit(name)
            if name in self._region_items:
                self.update_properties(self._region_items[name])

    def _on_pos_changed(self):
        if self._updating:
            return
        current = self.region_list.currentItem()
        if current and current.text() in self._region_items:
            item = self._region_items[current.text()]
            item.setPos(self.pos_x_spin.value(), self.pos_y_spin.value())

    def _on_rotation_changed(self):
        if self._updating:
            return
        current = self.region_list.currentItem()
        if current and current.text() in self._region_items:
            item = self._region_items[current.text()]
            item.setRotation(self.rotation_spin.value())
