# -*- coding: utf-8 -*-
"""
DateWheel控件
从 GUI.py 提取的模块
"""

from __future__ import annotations

import calendar
from datetime import date

from PySide6 import QtCore, QtWidgets

# 导入其他控件
from widgets.wheel_combo import WheelCombo


class DateWheel(QtWidgets.QWidget):
    """
    日期滚轮：年-月-日 三列。
    """
    valueChanged = QtCore.Signal(str)  # "YYYY-MM-DD"

    def __init__(self, default: date | None = None, parent=None):
        super().__init__(parent)
        if default is None:
            default = date.today()
        # 固定可选年份：2025-2030（移除 2024，新增 2027-2030）
        y_items = [str(y) for y in range(2025, 2031)]
        m_items = [f"{m:02d}" for m in range(1, 13)]
        # 先按 31 天填充，变动时再截断
        d_items = [f"{d:02d}" for d in range(1, 32)]

        self.year = WheelCombo(y_items)
        self.month = WheelCombo(m_items)
        self.day = WheelCombo(d_items)

        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(self.year)
        lay.addWidget(self.month)
        lay.addWidget(self.day)

        self.year.currentIndexChanged.connect(self._emit)
        self.month.currentIndexChanged.connect(self._on_month_changed)
        self.day.currentIndexChanged.connect(self._emit)

        # 初始化到 default
        if str(default.year) in y_items:
            self.year.setCurrentText(str(default.year))
        else:
            self.year.setCurrentText(y_items[0])
        self.month.setCurrentText(f"{default.month:02d}")
        self._on_month_changed()
        self.day.setCurrentText(f"{default.day:02d}")
        self._emit()

    def _on_month_changed(self):
        y = int(self.year.currentText())
        m = int(self.month.currentText())
        # 计算该月天数
        days = calendar.monthrange(y, m)[1]
        # 更新 day 列表
        self.day.clear()
        for d in range(1, days + 1):
            self.day.addItem(f"{d:02d}")
        # 若当前选择超过 days，则退回到最后一天；确保索引不为 -1
        cur_idx = self.day.currentIndex()
        if cur_idx < 0:
            cur_idx = 0
        self.day.setCurrentIndex(min(cur_idx, days - 1))
        self._emit()

    def _emit(self):
        y = self.year.currentText()
        m = self.month.currentText()
        d = self.day.currentText()
        self.valueChanged.emit(f"{y}-{m}-{d}")

    def value(self) -> str:
        y = self.year.currentText()
        m = self.month.currentText()
        d = self.day.currentText()
        return f"{y}-{m}-{d}"
