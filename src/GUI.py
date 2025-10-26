# -*- coding: utf-8 -*-
"""
琴房预定 GUI 包装器（基于 PySide6）
-------------------------------------------------
- 不修改核心逻辑，只调用 main.txt / main.py 中的 `book()` 与 `timer_run()`。
- 满足以下 UI / 交互与业务要求：
  1) “设置”弹窗：编辑 proxies、user_id、user_name、user_email、user_phone、theme；必填项用红色星号。
  2) 主界面：
     - target_time：采用“滚轮式”组件组合（日期 + 时分秒），并有“立即启动”复选框。
       默认值 = 当天 21:00:00。
     - Cookie：不直接展示具体内容，点击按钮弹窗粘贴/更新；主界面显示“上次更新时间”。
     - 预定请求：可动态添加多组；每组包含 place、start_time、end_time；
       place 提供下拉（可编辑，含自动补全）；start/end 使用“双圈时间轮盘”（小时轮 + 分钟轮），
       范围 06:00~23:00；确保开始 <= 结束。
       若单个请求 > 2 小时，自动拆分为多段（每段 ≤ 120 分钟）分别调用 `book()`。
       展示格式形如 “25-09-17 13:00 - 14:30”。
  3) 所有参数保存到 config.yaml（包括 cookie 及其上次更新时间）。
  4) 故障处理：只要返回字符串未包含以下四个子串之一，就每 200ms 重试一次：
     - "Cookie 过期"
     - "保存成功"
     - "手速太慢，该时间段已经被预订啦"
     - "请求失败, 检查网络、代理服务器或 VPN"
     命中上述四个子串之一时弹窗提醒并停止该请求重试。
  5) 多请求可以并行执行（线程），尽力卡点提交。

运行：
  python piano_booking_gui.py

依赖：
  - PySide6
  - PyYAML
"""

from __future__ import annotations

import os
import sys
import json
import time
import math
from dataclasses import dataclass, asdict
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple

# ---- 依赖检查 ----
try:
    from PySide6 import QtCore, QtGui, QtWidgets, QtNetwork
except Exception as e:
    print("未找到 PySide6，请先执行：pip install PySide6")
    raise

# 尝试导入 WebEngine（用于自动登录功能）
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    print("注意：未找到 QtWebEngine，自动登录功能将不可用。")
    print("如需使用自动登录功能，请执行：pip install PySide6-WebEngine")

try:
    import yaml
except Exception as e:
    print("未找到 PyYAML，请先执行：pip install pyyaml")
    raise

# ---- 资源/路径工具 ----
def app_base_dir() -> str:
    try:
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
    except Exception:
        pass
    return os.path.dirname(os.path.abspath(__file__))

def resource_path(rel: str) -> str:
    try:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, rel)
    except Exception:
        pass
    return os.path.join(app_base_dir(), rel)

# ---- 加载核心模块：book() / timer_run() 来自用户的 main.txt 或 main.py ----
def _load_core():
    """
    优先从同目录的 main.py / main.txt 加载（支持打包后的资源目录），否则尝试 import main。
    """
    # 1) 直接从文件加载（优先）：main.py / main.txt（资源路径）
    try:
        from importlib.machinery import SourceFileLoader
        for name in ("main.py", "main.txt"):
            cand = resource_path(name)
            if os.path.exists(cand):
                core = SourceFileLoader("cuhk_booking_core", cand).load_module()  # type: ignore[deprecated]
                if hasattr(core, "book") and hasattr(core, "timer_run"):
                    return core
    except Exception:
        pass

    # 2) 兜底：import main（若被打包为模块或在 sys.path 中）
    try:
        import importlib
        core = importlib.import_module("main")
        if hasattr(core, "book") and hasattr(core, "timer_run"):
            return core
    except Exception:
        pass

    raise ImportError("未找到核心文件 main.py 或 main.txt，或其缺少 book()/timer_run() 函数。")

CORE = _load_core()
book = CORE.book
timer_run = CORE.timer_run

# ---- 导入代理检测模块 ----
try:
    from proxy_detector import ProxyDetector
    PROXY_DETECTOR_AVAILABLE = True
except ImportError:
    PROXY_DETECTOR_AVAILABLE = False
    print("注意：未找到 proxy_detector.py，自动代理检测功能将不可用。")

# ---- UI 常量：地点列表（用于下拉与补全；与核心 FID_MAP 的 key 对应） ----
PLACES: List[str] = [
    "MPC319 管弦乐学部",
    "MPC320 管弦乐学部",
    "MPC321 室内乐琴房（GP）",
    "MPC322 室内乐琴房（UP）",
    "MPC323 管弦乐学部琴房",
    "MPC324 管弦乐学部琴房",
    "MPC325 管弦乐学部琴房（UP）",
    "MPC326 管弦乐学部琴房（UP）",
    "MPC327 管弦乐学部琴房（UP）",
    "MPC328 管弦乐学部琴房（UP）",
    "MPC329 管弦乐学部琴房（UP）",
    "MPC334 室内乐琴房（GP）",
    "MPC335 管弦乐学部琴房",
    "MPC336 管弦乐学部琴房",
    "MPC337 管弦乐学部琴房",
    "MPC401 管弦乐学部琴房",
    "MPC402 管弦乐学部琴房",
    "MPC403 管弦乐学部琴房",
    "MPC404 管弦乐学部琴房",
    "MPC405 管弦乐学部琴房",
    "MPC406 管弦乐学部琴房（UP）",
    "MPC407 管弦乐学部琴房",
    "MPC408 管弦乐学部琴房（UP）",
    "MPC409 管弦乐学部琴房（UP）",
    "MPC410 管弦乐学部琴房",
    "MPC411 管弦乐学部琴房",
    "MPC412 室内乐琴房（GP）",
    "MPC413 室内乐琴房（UP）",
    "MPC414 管弦乐学部琴房",
    "MPC415 管弦乐学部琴房（UP）",
    "MPC416 管弦乐学部琴房",
    "MPC417 管弦乐学部琴房（UP）",
    "MPC418 管弦乐学部琴房（GP）",
    "MPC419 管弦乐学部琴房（GP）",
    "MPC420 管弦乐学部琴房（GP）",
    "MPC421 管弦乐学部琴房",
    "MPC422 管弦乐学部琴房（GP）",
    "MPC423 管弦乐学部琴房",
    "MPC424 管弦乐学部琴房（GP）",
    "MPC425 室内乐琴房（GP）",
    "MPC426 管弦乐学部琴房",
    "MPC427 管弦乐学部琴房",
    "MPC428 管弦乐学部琴房",
    "MPC429 管弦乐学部琴房",
    "MPC430 管弦乐学部琴房",
    "MPC518 室内乐琴房（Double GP）",
    "MPC519 室内乐琴房（Double GP）",
    "MPC524室内乐琴房（Double GP）",
]

# ---- 配置持久化 ----
CONFIG_FILE = os.path.join(app_base_dir(), "config.yaml")

@dataclass
class RequestItemData:
    place: str = PLACES[0]
    date: str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")  # 默认：明天
    start: str = "19:00"
    end: str = "21:00"

@dataclass
class AppConfig:
    target_time: str = datetime.now().strftime("%Y-%m-%d 21:00:00")  # 当天 21:00:00
    start_immediately: bool = False

    proxies: str = ""  # 文本框中保存的原始字符串（JSON/YAML 皆可）
    cookie: str = ""
    cookie_updated_at: str = ""

    user_id: str = ""
    user_password: str = ""  # 用户密码（用于自动登录）
    user_name: str = ""
    user_email: str = ""
    user_phone: str = ""
    theme: str = "练琴"

    requests: List[RequestItemData] = None  # type: ignore

    def __post_init__(self):
        if self.requests is None:
            self.requests = [RequestItemData()]

class ConfigManager:
    @staticmethod
    def load(path: str = CONFIG_FILE) -> AppConfig:
        if not os.path.exists(path):
            return AppConfig()
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        # 兼容旧结构
        reqs = []
        for it in raw.get("requests", []):
            reqs.append(RequestItemData(**it))
        cfg = AppConfig(
            target_time=raw.get("target_time", datetime.now().strftime("%Y-%m-%d 21:00:00")),
            start_immediately=bool(raw.get("start_immediately", False)),
            proxies=raw.get("proxies", ""),
            cookie=raw.get("cookie", ""),
            cookie_updated_at=raw.get("cookie_updated_at", ""),
            user_id=raw.get("user_id", ""),
            user_password=raw.get("user_password", ""),
            user_name=raw.get("user_name", ""),
            user_email=raw.get("user_email", ""),
            user_phone=raw.get("user_phone", ""),
            theme=raw.get("theme", "练琴"),
            requests=reqs or [RequestItemData()],
        )
        return cfg

    @staticmethod
    def save(cfg: AppConfig, path: str = CONFIG_FILE):
        data = asdict(cfg)
        # dataclass 中的 RequestItemData 需要转为普通 dict
        data["requests"] = [asdict(r) for r in cfg.requests]
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

# ---- 工具函数 ----
# proxies 不再是必填项，因为直接连接（校园网内或 AnyConnect VPN）时不需要代理
REQUIRED_FIELDS = ("user_id", "user_password", "user_name", "user_email")  # 需求声明的必填项

def parse_proxies(raw: str) -> Optional[Dict[str, str]]:
    """
    朴素文本框 -> dict。支持 JSON / YAML 格式；也支持空串（返回 None）。
    示例：{"http": "10.101.28.225:9000", "https": "10.101.28.225:9000"}
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        # 先尝试 JSON
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    try:
        obj = yaml.safe_load(raw)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    # 最后兜底：支持 "host:port" 一行，自动映射为 http/https
    if ":" in raw and " " not in raw and "{" not in raw:
        return {"http": raw, "https": raw}
    return None

def hhmm_to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)

def minutes_to_hhmm(x: int) -> str:
    h = x // 60
    m = x % 60
    return f"{h:02d}:{m:02d}"

def split_to_slots(start_hm: str, end_hm: str, max_minutes: int = 120) -> List[Tuple[str, str]]:
    """把 [start, end]（同一天）拆成若干 <= max_minutes 的闭区间（左闭右开逻辑用于序列化为字符串时更易理解）。"""
    s = hhmm_to_minutes(start_hm)
    e = hhmm_to_minutes(end_hm)
    out = []
    cur = s
    while cur < e:
        nxt = min(cur + max_minutes, e)
        out.append((minutes_to_hhmm(cur), minutes_to_hhmm(nxt)))
        cur = nxt
    return out

# ---- “轮式”组合控件 ----
class WheelCombo(QtWidgets.QComboBox):
    """
    一个视觉上更接近“滚轮”的组合框：
      - 行高更大，当前值居中显示；
      - 支持鼠标滚轮连续调节；
      - 键盘上下键也可调整。
    这是“类似 iPhone 闹钟设定的纵向滚轮设计”的近似实现。
    """
    def __init__(self, items: List[str], parent=None):
        super().__init__(parent)
        self.setEditable(False)
        self.addItems(items)
        # 大字号 & 行高 + 中央高亮；下拉高度随项目数自适应（不至过长）
        approx_row_h = 28
        view_min_h = min(300, max(approx_row_h * min(len(items), 8), approx_row_h * 3))
        self.setStyleSheet(f"""
            QComboBox {{
                font-size: 16px; padding: 6px 12px;
            }}
            QComboBox QAbstractItemView {{
                selection-background-color: #3daee9;
                outline: 0;
                font-size: 16px;
                min-height: {view_min_h}px;
            }}
        """)
        self.setMaxVisibleItems(min(10, len(items)))
        self.setInsertPolicy(QtWidgets.QComboBox.NoInsert)

    def wheelEvent(self, e: QtGui.QWheelEvent) -> None:
        delta = e.angleDelta().y()
        if delta < 0:
            self.setCurrentIndex(min(self.currentIndex() + 1, self.count() - 1))
        elif delta > 0:
            self.setCurrentIndex(max(self.currentIndex() - 1, 0))

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
        import calendar
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

class TimeWheel(QtWidgets.QWidget):
    """
    时间滚轮：小时-分钟 两列；小时限制在 06~23；分钟 00~59。
    """
    valueChanged = QtCore.Signal(str)  # "HH:MM"

    def __init__(self, default: str = "19:00", parent=None):
        super().__init__(parent)
        h_items = [f"{h:02d}" for h in range(6, 24)]
        self.hh = WheelCombo(h_items)

        # 分钟：左右分栏 00/30 开关
        self._minute_toggle = MinuteToggle()

        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(self.hh)
        lay.addWidget(self._minute_toggle)

        self.hh.currentIndexChanged.connect(self._emit)
        self._minute_toggle.valueChanged.connect(self._emit)

        # 初始化
        if ":" in default:
            h, m = default.split(":")
            if h.isdigit() and m.isdigit():
                hi = max(6, min(23, int(h)))
                mi = int(m)
                # 就近修正到 00 或 30（<15 -> 00; 15~44 -> 30; >=45 -> 下一小时 00；23点>=45固定为23:30）
                if mi < 15:
                    mm = "00"
                elif mi < 45:
                    mm = "30"
                else:
                    if hi < 23:
                        hi += 1
                        mm = "00"
                    else:
                        mm = "30"
                self.hh.setCurrentText(f"{hi:02d}")
                self._minute_toggle.setValue(mm)
        self._emit()

        # 对齐分钟开关与小时滚轮的高度
        QtCore.QTimer.singleShot(0, lambda: self._minute_toggle.setButtonHeight(self.hh.sizeHint().height()))

    def value(self) -> str:
        return f"{self.hh.currentText()}:{self._minute_toggle.value()}"

    def setValue(self, hhmm: str):
        if ":" in hhmm:
            h, m = hhmm.split(":")
            try:
                hi = max(6, min(23, int(h)))
                mi = int(m)
            except Exception:
                return
            if mi < 15:
                mm = "00"
            elif mi < 45:
                mm = "30"
            else:
                if hi < 23:
                    hi += 1
                    mm = "00"
                else:
                    mm = "30"
            self.hh.setCurrentText(f"{hi:02d}")
            self._minute_toggle.setValue(mm)
        # 不主动触发 _emit，避免在外层处理 valueChanged 时造成递归；
        # 若值有变化，setCurrentText 自身会触发 currentIndexChanged 从而调用 _emit。

    def _emit(self):
        self.valueChanged.emit(self.value())

    # 供外部设置分钟控件的最小宽度（用于对齐）
    def setMinuteMinWidth(self, w: int):
        self._minute_toggle.setMinimumWidth(w)


class MinuteToggle(QtWidgets.QWidget):
    """
    左右分栏的分钟开关：两个并列按钮，分别为“00 分”和“30 分”，互斥选中。
    """
    valueChanged = QtCore.Signal(str)  # "00" or "30"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.btn00 = QtWidgets.QPushButton("00")
        self.btn30 = QtWidgets.QPushButton("30")
        for b in (self.btn00, self.btn30):
            b.setCheckable(True)
            b.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn00.setChecked(True)

        self.group = QtWidgets.QButtonGroup(self)
        self.group.setExclusive(True)
        self.group.addButton(self.btn00, 0)
        self.group.addButton(self.btn30, 1)

        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.btn00)
        lay.addWidget(self.btn30)

        # 分段按钮样式（类似 segmented control），选中高亮改为灰色
        self.setStyleSheet(
            """
            QPushButton { border: 1px solid #c8c8c8; padding: 6px 12px; font-size: 16px; }
            QPushButton:checked { background: #d0d0d0; color: #222; }
            QPushButton:!checked { background: #f7f7f7; color: #222; }
            QPushButton:first-child { border-top-left-radius: 6px; border-bottom-left-radius: 6px; }
            QPushButton:last-child { border-top-right-radius: 6px; border-bottom-right-radius: 6px; border-left: none; }
            """
        )

        self.group.idToggled.connect(self._on_toggled)

    def _on_toggled(self, _id: int, checked: bool):
        if not checked:
            return
        self.valueChanged.emit(self.value())

    def value(self) -> str:
        return "30" if self.btn30.isChecked() else "00"

    def setValue(self, v: str):
        v = (v or "00").strip()
        if v == "30":
            self.btn30.setChecked(True)
        else:
            self.btn00.setChecked(True)

    def setButtonHeight(self, h: int):
        try:
            h = int(h)
        except Exception:
            return
        for b in (self.btn00, self.btn30):
            b.setFixedHeight(h)

# ---- 单个请求编辑项 ----
class RequestItemWidget(QtWidgets.QFrame):
    removed = QtCore.Signal(object)  # self
    changed = QtCore.Signal()

    def __init__(self, data: RequestItemData | None = None, parent=None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setObjectName("RequestItem")
        self.setStyleSheet("""
            QFrame#RequestItem {
                border: 1px solid #dadada; border-radius: 8px; padding: 4px;
                background: #fcfcfc;
            }
            QComboBox { min-height: 26px; }
            QToolButton { min-height: 24px; min-width: 24px; }
        """)
        self.data = data or RequestItemData()

        # 地点：可编辑下拉 + 自动补全
        self.place = QtWidgets.QComboBox()
        self.place.setEditable(True)
        self.place.addItems(PLACES)
        self.place.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        completer = QtWidgets.QCompleter(PLACES, self.place)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.place.setCompleter(completer)
        self.place.setCurrentText(self.data.place)

        # 日期轮（默认明天）
        d = datetime.strptime(self.data.date, "%Y-%m-%d").date()
        self.date_wheel = DateWheel(default=d)

        # 双圈时间轮盘（开始/结束）
        self.start_wheel = TimeWheel(default=self.data.start)
        self.end_wheel = TimeWheel(default=self.data.end)
        # 加长未展开时的显示区（小时/分钟开关）
        for w in (self.start_wheel, self.end_wheel):
            w.hh.setMinimumWidth(84)
            w.setMinuteMinWidth(120)

        # 取消时间预览（根据需求）
        self.summary = None

        # 使开始/结束时间控件尺寸一致
        same_w = max(self.start_wheel.sizeHint().width(), self.end_wheel.sizeHint().width()) + 100
        self.start_wheel.setFixedWidth(same_w)
        self.end_wheel.setFixedWidth(same_w)

        self.btn_remove = QtWidgets.QToolButton()
        self.btn_remove.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogCancelButton))
        self.btn_remove.setToolTip("删除该组请求")

        # 布局
        g = QtWidgets.QGridLayout(self)
        g.setContentsMargins(4, 4, 4, 4)
        g.setHorizontalSpacing(6)
        g.setVerticalSpacing(2)
        r = 0
        _lbl_place = QtWidgets.QLabel("地点")
        _lbl_place.setStyleSheet("font-size:16px; font-weight:700;")
        g.addWidget(_lbl_place, r, 0, 1, 1)
        g.addWidget(self.place, r, 1, 1, 3)
        g.addWidget(self.btn_remove, r, 4, 1, 1, QtCore.Qt.AlignRight)
        r += 1

        _lbl_date = QtWidgets.QLabel("日期")
        _lbl_date.setStyleSheet("font-size:16px; font-weight:700;")
        g.addWidget(_lbl_date, r, 0)
        g.addWidget(self.date_wheel, r, 1, 1, 4)
        r += 1

        _lbl_start = QtWidgets.QLabel("开始时间")
        _lbl_start.setStyleSheet("font-size:16px; font-weight:700;")
        g.addWidget(_lbl_start, r, 0)
        g.addWidget(self.start_wheel, r, 1, 1, 2)
        _lbl_end = QtWidgets.QLabel("结束时间")
        _lbl_end.setStyleSheet("font-size:16px; font-weight:700;")
        g.addWidget(_lbl_end, r, 3)
        g.addWidget(self.end_wheel, r, 4, 1, 1)
        r += 1

        # 预览行取消
        # g.addWidget(QtWidgets.QLabel("预览"), r, 0)
        # g.addWidget(self.summary, r, 1, 1, 4)

        # 信号
        self.btn_remove.clicked.connect(lambda: self.removed.emit(self))
        self.place.currentTextChanged.connect(self._on_changed)
        self.date_wheel.valueChanged.connect(self._on_changed)
        self.start_wheel.valueChanged.connect(self._on_changed)
        self.end_wheel.valueChanged.connect(self._on_changed)

        self._on_changed()

    def to_data(self) -> RequestItemData:
        return RequestItemData(
            place=self.place.currentText().strip(),
            date=self.date_wheel.value(),
            start=self.start_wheel.value(),
            end=self.end_wheel.value(),
        )

    def _on_changed(self, *args):
        dd = self.to_data()
        # 校验：06:00~23:00 且 开始<=结束
        s = hhmm_to_minutes(dd.start)
        e = hhmm_to_minutes(dd.end)
        s = max(s, 6*60)
        e = min(e, 23*60)
        if e < s:
            e = s
        # 回写 wheel
        self.start_wheel.setValue(minutes_to_hhmm(s))
        self.end_wheel.setValue(minutes_to_hhmm(e))
        self.changed.emit()

# ---- 设置弹窗 ----
class SettingsDialog(QtWidgets.QDialog):
    saved = QtCore.Signal(object)  # AppConfig

    def __init__(self, cfg: AppConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setModal(True)
        self.cfg = cfg

        self.setMinimumWidth(520)

        # 字段
        def label(txt: str, required: bool = False):
            lab = QtWidgets.QLabel(txt + ("  " if not required else "  <span style='color:#e53935'>*</span>"))
            lab.setTextFormat(QtCore.Qt.RichText)
            return lab

        # 代理设置已移至 Cookie 对话框，这里不再显示

        self.le_uid = QtWidgets.QLineEdit(cfg.user_id)
        self.le_uid.setPlaceholderText("12XXXXXXX")

        self.le_pwd = QtWidgets.QLineEdit(cfg.user_password)
        self.le_pwd.setPlaceholderText("您的密码")
        self.le_pwd.setEchoMode(QtWidgets.QLineEdit.Password)

        self.le_uname = QtWidgets.QLineEdit(cfg.user_name)
        self.le_uname.setPlaceholderText("XXX")

        self.le_email = QtWidgets.QLineEdit(cfg.user_email)
        self.le_email.setPlaceholderText("example@link.cuhk.edu.cn")

        self.le_phone = QtWidgets.QLineEdit(cfg.user_phone)
        self.le_phone.setPlaceholderText("123456")

        self.le_theme = QtWidgets.QLineEdit(cfg.theme or "练琴")
        self.le_theme.setPlaceholderText("练琴")

        form = QtWidgets.QFormLayout()
        form.addRow(label("学号", True), self.le_uid)
        form.addRow(label("密码", True), self.le_pwd)
        form.addRow(label("姓名", True), self.le_uname)
        form.addRow(label("邮箱", True), self.le_email)
        form.addRow(label("电话"), self.le_phone)
        form.addRow(label("预定主题"), self.le_theme)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.on_save)
        btns.rejected.connect(self.reject)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(btns)

    def on_save(self):
        # 校验必填项
        missing = []
        if not (self.le_uid.text().strip()):
            missing.append("user_id")
        if not (self.le_pwd.text().strip()):
            missing.append("user_password")
        if not (self.le_uname.text().strip()):
            missing.append("user_name")
        if not (self.le_email.text().strip()):
            missing.append("user_email")
        if missing:
            QtWidgets.QMessageBox.warning(self, "缺少必填项", "请填写：" + "、".join(missing))
            return

        # 填充并发射（proxies 已移至 Cookie 对话框，这里不再处理）
        self.cfg.user_id = self.le_uid.text().strip()
        self.cfg.user_password = self.le_pwd.text().strip()
        self.cfg.user_name = self.le_uname.text().strip()
        self.cfg.user_email = self.le_email.text().strip()
        self.cfg.user_phone = self.le_phone.text().strip()
        self.cfg.theme = self.le_theme.text().strip() or "练琴"
        self.saved.emit(self.cfg)
        self.accept()

# ---- Cookie 与代理弹窗（合并）----
class CookieDialog(QtWidgets.QDialog):
    saved = QtCore.Signal(str, str)  # (cookie, proxies)

    def __init__(self, init_cookie: str, init_proxies: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cookie 与代理设置")
        self.setModal(True)
        self.setMinimumWidth(700)

        # === 代理设置区域 ===
        proxy_group = QtWidgets.QGroupBox("代理设置（自动获取）")
        proxy_group.setStyleSheet("QGroupBox { font-weight: bold; }")

        self.le_proxies = QtWidgets.QLineEdit(init_proxies or "")
        self.le_proxies.setPlaceholderText("自动检测或留空（校园网/VPN直连）")
        self.le_proxies.setReadOnly(True)  # 设置为只读，只能通过自动检测填充
        self.le_proxies.setStyleSheet("QLineEdit { background-color: #f0f0f0; }")

        self.btn_auto_detect = QtWidgets.QPushButton("🔄 自动检测代理")
        self.btn_auto_detect.clicked.connect(self.on_auto_detect_proxy)
        self.btn_auto_detect.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        proxy_layout = QtWidgets.QVBoxLayout()
        proxy_layout.addWidget(QtWidgets.QLabel("当前代理:"))
        proxy_layout.addWidget(self.le_proxies)
        proxy_layout.addWidget(self.btn_auto_detect)
        proxy_group.setLayout(proxy_layout)

        # === Cookie 设置区域 ===
        cookie_group = QtWidgets.QGroupBox("Cookie 设置（自动获取）")
        cookie_group.setStyleSheet("QGroupBox { font-weight: bold; }")

        self.text = QtWidgets.QPlainTextEdit(init_cookie or "")
        self.text.setPlaceholderText(
            "点击「自动登录获取」按钮自动获取 Cookie\n"
            "或手动粘贴 Cookie：\n"
            "示例：entry=normal; lang=zh_CN; jsession.id=...; JSESSIONID=...; pathname=/a/field/client/main"
        )
        self.text.setReadOnly(True)  # 暂时设置为只读
        self.text.setStyleSheet("QPlainTextEdit { background-color: #f0f0f0; }")
        self.text.setMaximumHeight(100)

        # 添加手动输入按钮
        self.btn_manual_input = QtWidgets.QPushButton("📝 手动输入 Cookie")
        self.btn_manual_input.clicked.connect(self.on_toggle_manual_input)

        cookie_layout = QtWidgets.QVBoxLayout()
        cookie_layout.addWidget(self.text)
        cookie_layout.addWidget(self.btn_manual_input)
        cookie_group.setLayout(cookie_layout)

        # === 按钮区域 ===
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.on_save)
        btns.rejected.connect(self.reject)

        # === 主布局 ===
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(proxy_group)
        lay.addWidget(cookie_group)
        lay.addWidget(btns)

    def on_toggle_manual_input(self):
        """切换手动输入模式"""
        if self.text.isReadOnly():
            self.text.setReadOnly(False)
            self.text.setStyleSheet("QPlainTextEdit { background-color: white; }")
            self.btn_manual_input.setText("🔒 锁定编辑")
        else:
            self.text.setReadOnly(True)
            self.text.setStyleSheet("QPlainTextEdit { background-color: #f0f0f0; }")
            self.btn_manual_input.setText("📝 手动输入 Cookie")

    def on_auto_detect_proxy(self):
        """点击"自动检测"按钮时调用"""
        if not PROXY_DETECTOR_AVAILABLE:
            QtWidgets.QMessageBox.warning(
                self, "功能不可用",
                "未找到 proxy_detector.py 模块，无法使用自动检测功能。"
            )
            return

        # 显示检测中提示
        self.btn_auto_detect.setEnabled(False)
        self.btn_auto_detect.setText("检测中...")

        # 禁用SSL警告
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except Exception:
            pass

        # 执行检测
        try:
            proxy_dict = ProxyDetector.auto_detect()
            proxy_str = ProxyDetector.format_for_config(proxy_dict)

            if proxy_dict:
                # 检测到需要使用代理
                self.le_proxies.setText(proxy_str)
                QtWidgets.QMessageBox.information(
                    self, "检测成功",
                    f"已检测到可用代理：\n{proxy_str}\n\n该代理已自动填入，点击「保存」应用。"
                )
            else:
                # 检测到可以直接连接（校园网内或 AnyConnect VPN）
                self.le_proxies.setText("")  # 清空代理设置
                QtWidgets.QMessageBox.information(
                    self, "检测成功",
                    "检测到可以直接连接到学校网站！\n\n"
                    "可能情况：\n"
                    "1. 您在校园网内\n"
                    "2. AnyConnect VPN 已连接\n\n"
                    "代理设置已清空，将使用直接连接。\n"
                    "点击「保存」应用。"
                )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "检测失败",
                f"自动检测网络配置时发生错误：\n{e}"
            )
        finally:
            # 恢复按钮状态
            self.btn_auto_detect.setEnabled(True)
            self.btn_auto_detect.setText("自动检测")

    def on_save(self):
        """保存 Cookie 和代理设置"""
        cookie = self.text.toPlainText().strip()
        proxies = self.le_proxies.text().strip()
        self.saved.emit(cookie, proxies)
        self.accept()


# ---- 自动登录对话框（需要 QtWebEngine）----
if WEBENGINE_AVAILABLE:
    class AutoLoginDialog(QtWidgets.QDialog):
        """自动登录并捕获Cookie的对话框"""
        cookie_captured = QtCore.Signal(str)  # 发送捕获到的Cookie字符串

        def __init__(self, proxies_config: str = "", user_id: str = "", user_password: str = "", parent=None):
            super().__init__(parent)
            self.setWindowTitle("自动登录 - CUHK 预订系统")
            self.setModal(True)
            self.resize(1024, 768)

            self.user_id = user_id
            self.user_password = user_password

            # 先创建 status_label（因为 _apply_proxy 会用到）
            self.status_label = QtWidgets.QLabel("正在初始化...")
            self.status_label.setStyleSheet("color: #666; font-size: 12px;")

            # ⚠️ 关键：在创建 Profile 之前先设置代理
            # QWebEngineProfile 创建时会使用当前的全局代理设置
            self._apply_proxy(proxies_config)

            # 创建独立的非持久化Profile（每次都是全新的，不保留Cookie）
            # 不作为子对象，避免删除顺序问题
            self.profile = QWebEngineProfile()

            # 启用开发者工具用于调试
            from PySide6.QtWebEngineCore import QWebEngineSettings
            self.profile.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            self.profile.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)

            # 清除所有Cookie（确保每次都是全新登录）
            self.cookie_store = self.profile.cookieStore()
            self.cookie_store.deleteAllCookies()

            # 创建自定义Page使用独立Profile
            self.page = QWebEnginePage(self.profile, self)

            # 创建WebEngineView并设置Page
            self.browser = QWebEngineView()
            self.browser.setPage(self.page)

            # UI组件（创建其他UI组件）
            self.url_bar = QtWidgets.QLineEdit()
            self.url_bar.setReadOnly(True)
            self.url_bar.setStyleSheet("padding: 4px; font-size: 12px;")

            self.progress_bar = QtWidgets.QProgressBar()
            self.progress_bar.setMaximumHeight(4)
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setStyleSheet("""
                QProgressBar { border: none; background: #f0f0f0; }
                QProgressBar::chunk { background: #3daee9; }
            """)

            self.btn_refresh = QtWidgets.QPushButton("刷新")
            self.btn_refresh.setMaximumWidth(80)

            self.btn_devtools = QtWidgets.QPushButton("开发者工具")
            self.btn_devtools.setMaximumWidth(100)

            self.btn_capture = QtWidgets.QPushButton("手动捕获Cookie并关闭")
            self.btn_capture.setStyleSheet("font-size: 14px; padding: 8px;")

            # 布局
            self._setup_ui()

            # 初始化状态标志
            self.captured_cookies = {}
            self._auto_captured = False
            self._auto_filled = False
            self._fill_retry_count = 0
            self._progressive_form_state = 'init'
            self.devtools_window = None
            self._page_load_timeout_timer = None
            self._auto_capture_fallback_timer = None  # Cookie自动捕获保险计时器

            # 信号连接（在加载页面之前）
            self._connect_signals()

            # Cookie监听
            self.cookie_store.cookieAdded.connect(self._on_cookie_added)

            # 立即开始加载页面（不延迟，因为代理已经设置好了）
            self.status_label.setText("正在连接到预订系统...")
            self.browser.setUrl(QtCore.QUrl("https://booking.cuhk.edu.cn"))

            # 设置页面加载超时（30秒）
            self._page_load_timeout_timer = QtCore.QTimer(self)
            self._page_load_timeout_timer.setSingleShot(True)
            self._page_load_timeout_timer.timeout.connect(self._on_page_load_timeout)
            self._page_load_timeout_timer.start(30000)

            # 设置Cookie自动捕获保险计时器（30秒后，如果还没自动捕获且有Cookie，就强制捕获）
            self._auto_capture_fallback_timer = QtCore.QTimer(self)
            self._auto_capture_fallback_timer.setSingleShot(True)
            self._auto_capture_fallback_timer.timeout.connect(self._fallback_auto_capture)
            self._auto_capture_fallback_timer.start(30000)  # 30秒保险

        def closeEvent(self, event):
            """对话框关闭时，确保正确的资源释放顺序"""
            # 停止所有计时器
            if self._page_load_timeout_timer and self._page_load_timeout_timer.isActive():
                self._page_load_timeout_timer.stop()

            if self._auto_capture_fallback_timer and self._auto_capture_fallback_timer.isActive():
                self._auto_capture_fallback_timer.stop()

            # 先断开 Browser 和 Page 的连接
            self.browser.setPage(None)

            # 删除 Page（必须在 Profile 之前删除）
            if hasattr(self, 'page') and self.page:
                self.page.deleteLater()
                self.page = None

            # 延迟删除 Profile（确保 Page 已经完全删除）
            if hasattr(self, 'profile') and self.profile:
                profile_to_delete = self.profile
                self.profile = None
                QtCore.QTimer.singleShot(100, profile_to_delete.deleteLater)

            super().closeEvent(event)

        def _on_page_load_timeout(self):
            """页面加载超时处理"""
            if self.progress_bar.value() < 100:
                self.status_label.setText("页面加载超时，请检查网络连接")
                QtWidgets.QMessageBox.warning(
                    self, "加载超时",
                    "页面加载超时，可能的原因：\n"
                    "1. 网络连接问题\n"
                    "2. 代理服务器未启动或配置错误\n"
                    "3. VPN未连接\n\n"
                    "请检查后重试或点击「刷新」按钮。"
                )

        def _apply_proxy(self, proxies_config: str):
            """应用代理设置（或明确禁用代理）"""
            try:
                # 如果没有配置代理，明确禁用代理（直接连接）
                if not proxies_config or not proxies_config.strip():
                    proxy = QtNetwork.QNetworkProxy()
                    proxy.setType(QtNetwork.QNetworkProxy.NoProxy)  # 🔑 关键：明确设置为无代理
                    QtNetwork.QNetworkProxy.setApplicationProxy(proxy)
                    # 只有在 status_label 存在时才设置文本
                    if hasattr(self, 'status_label'):
                        self.status_label.setText("使用直接连接（无代理）")
                    print("[AutoLoginDialog] 已设置为直接连接（NoProxy）")
                    return

                # 如果配置了代理，解析并应用
                proxies = parse_proxies(proxies_config)
                if proxies and "http" in proxies:
                    proxy_url = proxies["http"].replace("http://", "").replace("https://", "")
                    if ":" in proxy_url:
                        host, port = proxy_url.split(":", 1)
                        proxy = QtNetwork.QNetworkProxy()
                        proxy.setType(QtNetwork.QNetworkProxy.HttpProxy)
                        proxy.setHostName(host)
                        proxy.setPort(int(port))
                        QtNetwork.QNetworkProxy.setApplicationProxy(proxy)
                        # 只有在 status_label 存在时才设置文本
                        if hasattr(self, 'status_label'):
                            self.status_label.setText(f"已应用代理: {host}:{port}")
                        print(f"[AutoLoginDialog] 已应用代理: {host}:{port}")
                else:
                    # 配置格式错误，禁用代理
                    proxy = QtNetwork.QNetworkProxy()
                    proxy.setType(QtNetwork.QNetworkProxy.NoProxy)
                    QtNetwork.QNetworkProxy.setApplicationProxy(proxy)
                    # 只有在 status_label 存在时才设置文本
                    if hasattr(self, 'status_label'):
                        self.status_label.setText("代理配置无效，使用直接连接")
                    print("[AutoLoginDialog] 代理配置无效，已设置为直接连接")
            except Exception as e:
                # 出错时也禁用代理
                print(f"[Warning] Failed to apply proxy: {e}, using direct connection")
                proxy = QtNetwork.QNetworkProxy()
                proxy.setType(QtNetwork.QNetworkProxy.NoProxy)
                QtNetwork.QNetworkProxy.setApplicationProxy(proxy)
                # 只有在 status_label 存在时才设置文本
                if hasattr(self, 'status_label'):
                    self.status_label.setText("代理设置失败，使用直接连接")

        def _setup_ui(self):
            """布局设置"""
            # 顶部工具栏
            toolbar = QtWidgets.QHBoxLayout()
            toolbar.addWidget(QtWidgets.QLabel("地址:"))
            toolbar.addWidget(self.url_bar, 1)
            toolbar.addWidget(self.btn_refresh)
            toolbar.addWidget(self.btn_devtools)

            # 状态栏
            statusbar = QtWidgets.QHBoxLayout()
            statusbar.addWidget(self.status_label)
            statusbar.addStretch()

            # 主布局
            layout = QtWidgets.QVBoxLayout(self)
            layout.addLayout(toolbar)
            layout.addWidget(self.progress_bar)
            layout.addWidget(self.browser, 1)
            layout.addLayout(statusbar)
            layout.addWidget(self.btn_capture)

        def _connect_signals(self):
            """信号槽连接"""
            self.browser.urlChanged.connect(self._on_url_changed)
            self.browser.loadProgress.connect(self._on_load_progress)
            self.browser.loadFinished.connect(self._on_load_finished)
            self.btn_refresh.clicked.connect(self.browser.reload)
            self.btn_devtools.clicked.connect(self._open_devtools)
            self.btn_capture.clicked.connect(self._capture_and_close)

        def _on_cookie_added(self, cookie):
            """Cookie添加时的回调"""
            domain = cookie.domain()
            if "cuhk.edu.cn" in domain:
                try:
                    name = bytes(cookie.name()).decode('utf-8')
                    value = bytes(cookie.value()).decode('utf-8')
                    self.captured_cookies[name] = value
                    print(f"[AutoLogin] Cookie已捕获: {name}")

                    # 当捕获到足够的Cookie时（至少5个），尝试自动捕获
                    if len(self.captured_cookies) >= 5 and not self._auto_captured:
                        print(f"[AutoLogin] 已捕获 {len(self.captured_cookies)} 个Cookie，准备自动验证...")
                        QtCore.QTimer.singleShot(1000, self._auto_capture)
                except Exception as e:
                    print(f"[Warning] Failed to decode cookie: {e}")

        def _on_url_changed(self, url):
            """URL变化时更新地址栏并检查是否登录成功"""
            url_str = url.toString()
            self.url_bar.setText(url_str)
            print(f"[AutoLogin] URL变化: {url_str}")

            # 检测登录成功的URL特征（扩展的智能登录检测）
            success_patterns = [
                "/field/client/main",
                "/field/book",
                "/sso/code",
                "/a/field/",
                "booking.cuhk.edu.cn/a/",
                "jsessionid=",  # URL中包含session ID
            ]

            is_login_success = any(pattern.lower() in url_str.lower() for pattern in success_patterns)

            if not self._auto_captured and is_login_success:
                print(f"[AutoLogin] 检测到登录成功URL: {url_str}")
                self.status_label.setText("检测到登录成功，正在捕获Cookie...")
                # 延迟2秒等待Cookie完全加载，然后自动捕获
                QtCore.QTimer.singleShot(2000, self._auto_capture)
            elif not self._auto_filled and self.user_id and self.user_password:
                # URL变化时也尝试自动填写（可能跳转到了登录页）
                # 延迟1秒确保页面加载完成
                self._fill_retry_count = 0  # 重置重试计数
                QtCore.QTimer.singleShot(1000, self._try_auto_fill_form)

        def _on_load_progress(self, progress):
            """更新加载进度"""
            self.progress_bar.setValue(progress)
            if progress < 100:
                self.status_label.setText(f"加载中... {progress}%")

        def _on_load_finished(self, ok):
            """页面加载完成/失败"""
            # 停止超时计时器
            if self._page_load_timeout_timer and self._page_load_timeout_timer.isActive():
                self._page_load_timeout_timer.stop()

            if ok:
                self.progress_bar.setValue(100)
                self.status_label.setText("页面加载完成")

                # 如果有用户名密码，且未自动填写过，尝试自动填写
                # 延迟1秒确保页面JavaScript完全执行
                if self.user_id and self.user_password and not self._auto_filled:
                    self.status_label.setText("页面加载完成，准备自动填写表单...")
                    QtCore.QTimer.singleShot(1000, self._try_auto_fill_form)
            else:
                self.progress_bar.setValue(0)
                error_msg = "页面加载失败，请检查：\n" \
                            "1. 网络连接是否正常\n" \
                            "2. 代理服务器是否可用\n" \
                            "3. 是否在校园网内"
                self.status_label.setText("加载失败")
                QtWidgets.QMessageBox.warning(self, "加载错误", error_msg)

        def _try_auto_fill_form(self):
            """尝试自动填写登录表单（支持渐进式表单）"""
            if self._auto_filled:
                return

            # JavaScript代码：支持渐进式表单的自动填写
            js_code = f"""
            (function() {{
                console.log('[AutoLogin] Starting form auto-fill (state: {self._progressive_form_state})...');
                console.log('[AutoLogin] Current URL: ' + window.location.href);

                // 步骤1：查找并点击"Login"按钮（如果表单未显示）
                if ('{self._progressive_form_state}' === 'init') {{
                    console.log('[AutoLogin] Step 1: Looking for Login button...');
                    var loginButtons = document.querySelectorAll('button, a, div[role="button"], span[role="button"]');
                    for (var i = 0; i < loginButtons.length; i++) {{
                        var btnText = (loginButtons[i].textContent || loginButtons[i].innerText || '').toLowerCase().trim();
                        console.log('[AutoLogin] Button [' + i + ']: "' + btnText + '"');
                        if (btnText === 'login' || btnText === '登录' || btnText === 'log in') {{
                            console.log('[AutoLogin] Found Login button, clicking...');
                            loginButtons[i].click();
                            return 'clicked_login';
                        }}
                    }}
                    console.log('[AutoLogin] Login button not found, looking for input fields...');
                }}

                // 步骤2：查找并填写用户名输入框
                var usernameField = document.querySelector('input[type="text"], input[type="email"], input[placeholder*="账号"], input[placeholder*="用户名"], input[placeholder*="学号"], input:not([type="password"]):not([type="hidden"]):not([type="submit"])');
                var passwordField = document.querySelector('input[type="password"]');

                console.log('[AutoLogin] Username field found: ' + (usernameField !== null));
                console.log('[AutoLogin] Password field found: ' + (passwordField !== null));

                // 如果只找到用户名框（没有密码框），先填写用户名
                if (usernameField && !passwordField && '{self._progressive_form_state}' !== 'filled_username') {{
                    console.log('[AutoLogin] Step 2: Filling username only...');

                    // 先聚焦输入框
                    usernameField.focus();
                    usernameField.value = '{self.user_id}';

                    // 触发所有必要的事件
                    ['input', 'change', 'blur', 'keyup'].forEach(function(eventType) {{
                        usernameField.dispatchEvent(new Event(eventType, {{ bubbles: true }}));
                    }});

                    console.log('[AutoLogin] Username filled: "' + usernameField.value + '"');

                    // 再次聚焦确保焦点正确
                    usernameField.focus();
                    usernameField.select();  // 选中文本

                    console.log('[AutoLogin] Looking for buttons on page...');

                    // 查找所有可能的按钮并输出它们的文本
                    var allButtons = document.querySelectorAll('button, a[href], div[onclick], span[onclick], input[type="submit"], input[type="button"]');
                    console.log('[AutoLogin] Found ' + allButtons.length + ' total buttons/links');

                    for (var i = 0; i < allButtons.length; i++) {{
                        var elem = allButtons[i];
                        var btnText = (elem.textContent || elem.innerText || elem.value || '').trim();
                        var btnHref = elem.href || '';
                        var btnOnclick = elem.onclick ? 'has onclick' : '';
                        console.log('[AutoLogin] Button [' + i + ']: text="' + btnText + '", tag=' + elem.tagName + ', href=' + btnHref + ', ' + btnOnclick);

                        // 匹配更多可能的按钮文本（中英文、大小写不敏感）
                        var lowerText = btnText.toLowerCase();
                        if (lowerText.includes('next') || lowerText.includes('下一步') || lowerText.includes('继续') ||
                            lowerText.includes('continue') || lowerText.includes('确定') || lowerText.includes('ok') ||
                            lowerText.includes('登录') || lowerText.includes('login') || lowerText.includes('提交') ||
                            lowerText.includes('submit') || lowerText.includes('进入') || lowerText.includes('enter')) {{
                            console.log('[AutoLogin] ✓ Found matching button! Clicking: "' + btnText + '"');
                            elem.click();
                            return 'filled_username_with_button';
                        }}
                    }}

                    console.log('[AutoLogin] No matching button found. Will press Enter key.');
                    return 'filled_username_need_enter';
                }}

                // 步骤3：如果同时有用户名和密码框，填写两者
                if (usernameField && passwordField) {{
                    console.log('[AutoLogin] Step 3: Filling both username and password...');

                    // 先填写用户名
                    usernameField.focus();
                    usernameField.value = '{self.user_id}';
                    ['input', 'change', 'blur', 'keyup'].forEach(function(eventType) {{
                        usernameField.dispatchEvent(new Event(eventType, {{ bubbles: true }}));
                    }});

                    // 再填写密码
                    passwordField.focus();
                    passwordField.value = '{self.user_password}';
                    ['input', 'change', 'blur', 'keyup'].forEach(function(eventType) {{
                        passwordField.dispatchEvent(new Event(eventType, {{ bubbles: true }}));
                    }});

                    console.log('[AutoLogin] Both fields filled: username="' + usernameField.value + '", password=' + ('*'.repeat(passwordField.value.length)));

                    // 再次聚焦密码框并选中
                    passwordField.focus();
                    passwordField.select();  // 选中文本

                    console.log('[AutoLogin] Looking for all buttons on page...');

                    // 查找所有可能的按钮（扩大范围）
                    var allButtons = document.querySelectorAll('button, a[href], div[onclick], span[onclick], input[type="submit"], input[type="button"], [role="button"]');
                    console.log('[AutoLogin] Found ' + allButtons.length + ' total buttons/links');

                    for (var i = 0; i < allButtons.length; i++) {{
                        var elem = allButtons[i];
                        var btnText = (elem.textContent || elem.innerText || elem.value || '').trim();
                        var btnId = elem.id || '';
                        var btnClass = elem.className || '';

                        console.log('[AutoLogin] Button [' + i + ']: text="' + btnText + '", id="' + btnId + '", class="' + btnClass + '"');

                        // 匹配登录按钮（检查文本、ID、class）
                        var lowerText = btnText.toLowerCase();
                        var lowerIdClass = (btnId + ' ' + btnClass).toLowerCase();

                        if (lowerText.includes('登录') || lowerText.includes('login') ||
                            lowerText.includes('sign in') || lowerText.includes('提交') ||
                            lowerText.includes('submit') || elem.type === 'submit' ||
                            lowerIdClass.includes('login') || lowerIdClass.includes('submit')) {{
                            console.log('[AutoLogin] ✓ Found Login button! Clicking: "' + btnText + '" (id=' + btnId + ')');
                            elem.click();
                            return 'filled_both_with_button';
                        }}
                    }}

                    console.log('[AutoLogin] No Login button found. Will press Enter key.');
                    return 'filled_both_need_enter';
                }}

                console.log('[AutoLogin] No actionable elements found');
                return 'not_found';
            }})();
            """

            def on_result(result):
                if result == 'clicked_login':
                    self._progressive_form_state = 'clicked_login'
                    self.status_label.setText('已点击Login按钮，等待表单加载...')
                    QtCore.QTimer.singleShot(1000, self._try_auto_fill_form)

                elif result == 'filled_username_with_button':
                    self._progressive_form_state = 'filled_username'
                    self.status_label.setText('已填写学号并点击"下一步"按钮，等待密码框出现...')
                    # 等待1秒后检查密码框是否出现
                    QtCore.QTimer.singleShot(1000, self._try_auto_fill_form)

                elif result == 'filled_username_need_enter':
                    self._progressive_form_state = 'filled_username'
                    self.status_label.setText('已填写学号，正在按回车键...')
                    # 延迟500ms后按第一次回车
                    QtCore.QTimer.singleShot(500, lambda: self._press_enter_key(2))

                elif result == 'filled_both_with_button':
                    self._auto_filled = True
                    self._progressive_form_state = 'completed'
                    self.status_label.setText('已填写学号和密码并点击"登录"按钮，等待登录完成...')
                    # 不需要额外操作，等待URL变化自动捕获Cookie

                elif result == 'filled_both_need_enter':
                    self._auto_filled = True
                    self._progressive_form_state = 'completed'
                    self.status_label.setText('已填写学号和密码，正在按回车键登录...')
                    # 延迟500ms后按回车
                    QtCore.QTimer.singleShot(500, lambda: self._press_enter_key(1))

                else:
                    # 未能找到元素时，延迟2秒后重试，最多重试5次
                    self._fill_retry_count += 1
                    if self._fill_retry_count <= 5 and not self._auto_filled:
                        self.status_label.setText(f"未找到可操作元素，{2}秒后重试...（第{self._fill_retry_count}/5次）")
                        QtCore.QTimer.singleShot(2000, self._try_auto_fill_form)
                    else:
                        self.status_label.setText("自动登录失败，请手动操作")

            self.page.runJavaScript(js_code, on_result)

        def _press_enter_key(self, count=1):
            """按回车键（支持多次）"""
            js_code = """
            (function() {{
                console.log('[AutoLogin] Pressing Enter key...');
                var activeElement = document.activeElement;

                if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {{
                    console.log('[AutoLogin] Active element is: ' + activeElement.tagName + ', type: ' + activeElement.type);

                    // 确保输入框被选中
                    activeElement.select();

                    // 按回车键
                    activeElement.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true }}));
                    activeElement.dispatchEvent(new KeyboardEvent('keypress', {{ key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true }}));
                    activeElement.dispatchEvent(new KeyboardEvent('keyup', {{ key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true }}));

                    console.log('[AutoLogin] Enter key pressed on ' + activeElement.type);
                    return 'pressed';
                }} else {{
                    console.log('[AutoLogin] No active input element found');
                    if (activeElement) {{
                        console.log('[AutoLogin] Current active element: ' + activeElement.tagName);
                    }}
                    return 'no_active_element';
                }}
            }})();
            """

            def on_enter_pressed(result):
                if result == 'pressed':
                    if count > 1:
                        # 如果需要按多次，延迟500ms后继续按
                        self.status_label.setText(f'已按第{2 - count + 1}次回车，准备按第{2 - count + 2}次...')
                        QtCore.QTimer.singleShot(500, lambda: self._press_enter_key(count - 1))
                    else:
                        self.status_label.setText('已按回车，等待登录完成...')
                        # 标记为已填写，避免重复填写
                        self._auto_filled = True
                else:
                    print('[AutoLogin] Failed to press Enter - no active input element')
                    self.status_label.setText('按回车失败，焦点不在输入框上')

            self.page.runJavaScript(js_code, on_enter_pressed)

        def _validate_cookie(self, cookie_dict: dict) -> bool:
            """验证Cookie是否完整（必须包含关键认证字段）"""
            print(f"[AutoLogin] 验证Cookie，当前有 {len(cookie_dict)} 个: {list(cookie_dict.keys())}")

            # 关键认证字段（必须至少有一个）
            critical_auth_fields = ["MSISAuth", "MSISAuthenticated", "JSESSIONID"]

            # 检查是否有关键认证字段
            has_critical_auth = False
            for field in critical_auth_fields:
                if field in cookie_dict:
                    print(f"[AutoLogin] [OK] 找到关键认证Cookie: {field}")
                    has_critical_auth = True
                    break

            if not has_critical_auth:
                print(f"[AutoLogin] [FAIL] 缺少关键认证Cookie (MSISAuth/MSISAuthenticated/JSESSIONID)")
                return False

            # 检查Cookie数量（至少需要5个Cookie才算完整）
            if len(cookie_dict) < 5:
                print(f"[AutoLogin] [FAIL] Cookie数量不足 ({len(cookie_dict)}/5)")
                return False

            print(f"[AutoLogin] [OK] Cookie验证通过！共{len(cookie_dict)}个")
            return True

        def _auto_capture(self):
            """自动捕获Cookie（严格验证，确保完整性）"""
            if self._auto_captured:
                print("[AutoLogin] 已经捕获过Cookie，跳过")
                return

            print(f"[AutoLogin] 尝试自动捕获，当前Cookie数量: {len(self.captured_cookies)}")

            # 严格验证：必须有关键认证字段且至少5个Cookie
            if self.captured_cookies and len(self.captured_cookies) >= 5:
                if self._validate_cookie(self.captured_cookies):
                    cookie_str = "; ".join([f"{k}={v}" for k, v in self.captured_cookies.items()])
                    self._auto_captured = True
                    print(f"[AutoLogin] Cookie捕获成功！共{len(self.captured_cookies)}个Cookie，{len(cookie_str)}个字符")
                    self.status_label.setText(f"Cookie捕获成功！共{len(self.captured_cookies)}个，正在关闭...")
                    self.cookie_captured.emit(cookie_str)
                    # 延迟200ms后自动关闭对话框，让用户看到成功提示
                    QtCore.QTimer.singleShot(200, self.accept)
                else:
                    print("[AutoLogin] Cookie验证失败，等待关键认证Cookie")
                    self.status_label.setText("Cookie不完整，等待关键认证字段...")
            else:
                print(f"[AutoLogin] Cookie数量不足({len(self.captured_cookies)}/5)，等待中...")
                self.status_label.setText(f"正在收集Cookie...({len(self.captured_cookies)}/5)")

        def _fallback_auto_capture(self):
            """保险机制：30秒后强制捕获Cookie（如果还没自动捕获）"""
            if self._auto_captured:
                print("[AutoLogin] Cookie已自动捕获，跳过保险机制")
                return

            if len(self.captured_cookies) >= 5:
                print("[AutoLogin] 保险机制触发：强制捕获Cookie")
                self.status_label.setText("正在强制捕获Cookie...")
                self._auto_capture()
            else:
                print(f"[AutoLogin] 保险机制触发但Cookie不足({len(self.captured_cookies)}/5)")
                self.status_label.setText(f"Cookie数量不足({len(self.captured_cookies)}/5)，请等待或手动操作")

        def _capture_and_close(self):
            """手动捕获Cookie并关闭对话框"""
            if not self.captured_cookies:
                QtWidgets.QMessageBox.warning(
                    self, "未检测到Cookie",
                    "请先登录预订系统，确保已成功访问 booking.cuhk.edu.cn"
                )
                return

            if not self._validate_cookie(self.captured_cookies):
                QtWidgets.QMessageBox.warning(
                    self, "Cookie不完整",
                    "捕获的Cookie缺少必要字段，可能是因为：\n"
                    "1. 尚未成功登录\n"
                    "2. 登录已过期\n\n"
                    "请重新登录后再试。"
                )
                return

            # 拼接Cookie字符串
            cookie_str = "; ".join([f"{k}={v}" for k, v in self.captured_cookies.items()])
            self.cookie_captured.emit(cookie_str)
            self.accept()

        def _open_devtools(self):
            """打开开发者工具窗口"""
            if not hasattr(self, 'devtools_window') or not self.devtools_window:
                # 创建开发者工具窗口
                self.devtools_window = QtWidgets.QDialog(self)
                self.devtools_window.setWindowTitle("开发者工具")
                self.devtools_window.resize(1024, 600)

                # 创建开发者工具视图
                from PySide6.QtWebEngineCore import QWebEnginePage
                self.devtools_view = QWebEngineView()

                # 设置页面的开发者工具页面
                self.page.setDevToolsPage(self.devtools_view.page())

                # 布局
                layout = QtWidgets.QVBoxLayout(self.devtools_window)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.devtools_view)

                # 添加说明标签
                info_label = QtWidgets.QLabel("提示：在Console标签中可以看到 [AutoLogin] 开头的调试日志")
                info_label.setStyleSheet("background: #ffffcc; padding: 8px; font-size: 12px;")
                layout.insertWidget(0, info_label)

            # 显示窗口
            self.devtools_window.show()
            self.devtools_window.raise_()
            self.devtools_window.activateWindow()
            self.status_label.setText("开发者工具已打开，请查看Console标签")
else:
    # 如果 QtWebEngine 不可用，创建一个占位类
    class AutoLoginDialog:
        def __init__(self, *args, **kwargs):
            raise ImportError("QtWebEngine 模块不可用，无法使用自动登录功能。请安装：pip install PySide6-WebEngine")

# ---- 预定执行线程 ----
class BookingWorker(QtCore.QThread):
    log = QtCore.Signal(str)
    popup = QtCore.Signal(str, str)   # (level, message) level in {"info","warn","error"}
    finished_all = QtCore.Signal()

    def __init__(self, cfg: AppConfig, chunks: List[Tuple[str, str, str]], parent=None):
        """
        :param chunks: [(place, start_ts, end_ts)]，ts 格式 "YYYY-MM-DD HH:MM"
        """
        super().__init__(parent)
        self.cfg = cfg
        self.chunks = chunks
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def _try_once(self, place: str, start_ts: str, end_ts: str) -> str:
        return book(
            cookie=self.cfg.cookie,
            user_id=self.cfg.user_id,
            user_name=self.cfg.user_name,
            place=place,
            start_time=start_ts,
            end_time=end_ts,
            user_email=self.cfg.user_email,
            user_phone=self.cfg.user_phone,
            theme=self.cfg.theme or "练琴",
            proxies=parse_proxies(self.cfg.proxies),
        )

    def run(self):
        MUST_STOP = ["Cookie 过期", "保存成功", "手速太慢，该时间段已经被预订啦", "请求失败, 检查网络、代理服务器或 VPN"]
        for (place, start_ts, end_ts) in self.chunks:
            if self._stop_flag:
                break
            self.log.emit(f"开始预定：{place}  {start_ts} - {end_ts}")
            # 重试直到命中 MUST_STOP 之一
            while not self._stop_flag:
                try:
                    msg = self._try_once(place, start_ts, end_ts)
                except Exception as e:
                    msg = f"异常：{e!r}"

                self.log.emit(f"返回：{msg}")
                if any(key in msg for key in MUST_STOP):
                    # 弹窗
                    if "保存成功" in msg:
                        self.popup.emit("info", f"保存成功：{place}  {start_ts} - {end_ts}")
                    elif "手速太慢" in msg:
                        self.popup.emit("warn", f"已被预订：{place}  {start_ts} - {end_ts}")
                    elif "Cookie 过期" in msg:
                        self.popup.emit("error", "Cookie 过期，请在右上角按钮中重新设置 Cookie。")
                    elif "请求失败" in msg:
                        self.popup.emit("error", "请求失败，请检查网络、代理服务器或 VPN。")
                    break
                time.sleep(0.2)
        self.finished_all.emit()

# ---- 主窗口 ----
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # 软件标题改为“魔丸”
        self.setWindowTitle("魔丸")
        # 左上角图标设置为 CCA.ico（需与可执行放同目录）
        try:
            self.setWindowIcon(QtGui.QIcon(resource_path("CCA.ico")))
        except Exception:
            pass

        # 样式（Fusion + 轻量美化 + 全局字体）
        QtWidgets.QApplication.setStyle("Fusion")
        app = QtWidgets.QApplication.instance()
        if app is not None:
            # 尝试加载打包内字体
            try:
                QPF = QtGui.QFontDatabase
                fonts_dir = resource_path("fonts")
                for fname in ("FiraCode-Regular.ttf", "FangZhengXinShuSongJianTi-1.ttf"):
                    fpath = os.path.join(fonts_dir, fname)
                    if os.path.exists(fpath):
                        QPF.addApplicationFont(fpath)
            except Exception:
                pass

            font = app.font()
            font.setFamily("Fira Code, 方正新书宋简体")
            app.setFont(font)
            app.setStyleSheet("* { font-family: 'Fira Code','方正新书宋简体'; }")
        self.setMinimumSize(920, 680)

        # 配置
        self.cfg = ConfigManager.load()

        # 启动时自动检测代理（如果proxies为空或检测失败）
        self._auto_detect_proxy_on_startup()

        # 顶部工具栏：设置、Cookie
        self.btn_settings = QtWidgets.QToolButton()
        self.btn_settings.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogDetailedView))
        self.btn_settings.setToolTip("设置（proxies / 用户信息 / 主题）")

        self.btn_cookie = QtWidgets.QToolButton()
        self.btn_cookie.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogOpenButton))
        self.btn_cookie.setToolTip("设置 Cookie")

        self.cookie_info = QtWidgets.QLabel(self._cookie_summary())
        self.cookie_info.setStyleSheet("color:#777;")

        topbar = QtWidgets.QHBoxLayout()
        topbar.addWidget(self.btn_settings)
        topbar.addWidget(self.btn_cookie)
        topbar.addWidget(self.cookie_info)
        topbar.addStretch()

        # 目标时间（滚轮）+ 立即启动
        tgt_group = QtWidgets.QGroupBox("启动时间")
        # 放大并加粗“启动时间”标题
        tgt_group.setStyleSheet("QGroupBox::title { font-size: 18px; font-weight: 700; }")
        tgt_lay = QtWidgets.QHBoxLayout(tgt_group)

        # 日期轮 + 时间轮（秒也支持）
        target_dt = datetime.strptime(self.cfg.target_time, "%Y-%m-%d %H:%M:%S")
        self.target_date = DateWheel(default=target_dt.date())
        h_items = [f"{h:02d}" for h in range(0, 24)]
        m_items = [f"{m:02d}" for m in range(0, 60)]
        s_items = [f"{s:02d}" for s in range(0, 60)]
        self.target_h = WheelCombo(h_items)
        self.target_m = WheelCombo(m_items)
        self.target_s = WheelCombo(s_items)
        self.target_h.setCurrentText(f"{target_dt.hour:02d}")
        self.target_m.setCurrentText(f"{target_dt.minute:02d}")
        self.target_s.setCurrentText(f"{target_dt.second:02d}")

        tgt_lay.addWidget(self.target_date, 3)
        tgt_lay.addWidget(self.target_h, 1)
        tgt_lay.addWidget(self.target_m, 1)
        tgt_lay.addWidget(self.target_s, 1)

        self.cb_immediate = QtWidgets.QCheckBox("立即启动")
        self.cb_immediate.setChecked(self.cfg.start_immediately)
        tgt_lay.addWidget(self.cb_immediate)

        # 请求列表
        self.req_container = QtWidgets.QWidget()
        self.req_vbox = QtWidgets.QVBoxLayout(self.req_container)
        self.req_vbox.setContentsMargins(0, 0, 0, 0)
        self.req_vbox.setSpacing(4)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.req_container)

        self.btn_add = QtWidgets.QPushButton("＋ 添加一组预定请求")
        self.btn_add.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        # 日志 + 启动
        self.te_log = QtWidgets.QPlainTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setPlaceholderText("运行日志将在此显示…")

        self.btn_start = QtWidgets.QPushButton("开始")
        # 顶边不变，底边与左侧组框对齐：垂直方向可扩展
        self.btn_start.setMinimumHeight(44)
        self.btn_start.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self.btn_start.setStyleSheet("font-size:22px; font-weight:600;")

        # 主布局
        central = QtWidgets.QWidget()
        main = QtWidgets.QVBoxLayout(central)
        main.setContentsMargins(16, 12, 16, 12)
        main.setSpacing(8)
        main.addLayout(topbar)
        tgt_row = QtWidgets.QHBoxLayout()
        tgt_row.addWidget(tgt_group, 4)
        # 把“开始”按钮放在目标时间旁边
        tgt_row.addWidget(self.btn_start, 1)
        main.addLayout(tgt_row)
        main.addWidget(self.scroll, 2)
        main.addWidget(self.btn_add, 0)
        # 运行日志高度小一些
        self.te_log.setMaximumHeight(160)
        main.addWidget(self.te_log, 1)
        self.setCentralWidget(central)

        # 信号
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_cookie.clicked.connect(self.open_cookie)
        self.btn_add.clicked.connect(self.add_request_item)
        self.btn_start.clicked.connect(self.on_start_clicked)

        # 载入配置中的请求
        for r in self.cfg.requests:
            self.add_request_item(r)

        # 状态
        self.worker = None
        self.scheduled_timer = None  # threading.Timer 来自用户 core.timer_run()
        self.qt_timer = None         # Qt 定时器，保障到点必触发
        self._has_started = False    # 防止重复触发

    # --- helpers ---
    def _cookie_summary(self) -> str:
        if self.cfg.cookie and self.cfg.cookie_updated_at:
            return f"Cookie 已设置，最近更新时间：{self.cfg.cookie_updated_at}"
        elif self.cfg.cookie:
            return f"Cookie 已设置"
        else:
            return "Cookie 未设置"

    def _auto_detect_proxy_on_startup(self):
        """启动时自动检测网络配置（优先检测Reqable代理）"""
        if not PROXY_DETECTOR_AVAILABLE:
            return

        print("[启动] 开始自动检测网络配置（优先检测Reqable）...")

        # 禁用SSL警告
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except Exception:
            pass

        # 自动检测网络配置（总是执行，不跳过）
        try:
            proxy_dict = ProxyDetector.auto_detect()
            proxy_str = ProxyDetector.format_for_config(proxy_dict)

            if proxy_dict:
                # 检测到代理（Reqable等）
                self.cfg.proxies = proxy_str
                ConfigManager.save(self.cfg)
                print(f"[启动] [OK] 已自动检测并应用代理: {proxy_str}")
            else:
                # 可以直接连接（校园网或VPN）
                self.cfg.proxies = ""
                ConfigManager.save(self.cfg)
                print("[启动] [OK] 检测到可以直接连接（校园网内或 AnyConnect VPN）")
                print("[启动] [WARNING] 注意：booking接口可能需要Reqable代理才能正常工作")
        except Exception as e:
            print(f"[启动] [ERROR] 自动检测网络配置失败: {e}")

    def add_request_item(self, data: RequestItemData | None = None):
        item = RequestItemWidget(data)
        item.removed.connect(self._remove_request_item)
        item.changed.connect(self._save_requests_snapshot)
        self.req_vbox.addWidget(item)
        # 若当前只有一组请求，进一步压缩其内部间距
        if len(self._iter_items()) == 1:
            # 缩小该卡片的外边距/行距
            w: RequestItemWidget = item
            lay = w.layout()
            if isinstance(lay, QtWidgets.QGridLayout):
                lay.setContentsMargins(2, 2, 2, 2)
                lay.setHorizontalSpacing(4)
                lay.setVerticalSpacing(1)
        self._save_requests_snapshot()

    def _remove_request_item(self, item: RequestItemWidget):
        item.setParent(None)
        item.deleteLater()
        self._save_requests_snapshot()

    def _iter_items(self) -> List[RequestItemWidget]:
        res = []
        for i in range(self.req_vbox.count()):
            w = self.req_vbox.itemAt(i).widget()
            if isinstance(w, RequestItemWidget):
                res.append(w)
        return res

    def _save_requests_snapshot(self):
        reqs: List[RequestItemData] = [w.to_data() for w in self._iter_items()]
        self.cfg.requests = reqs
        # 同步保存 config（避免意外退出丢失）
        self.cfg.target_time = self.current_target_time()
        self.cfg.start_immediately = self.cb_immediate.isChecked()
        ConfigManager.save(self.cfg)

    def current_target_time(self) -> str:
        ymd = self.target_date.value()
        h = self.target_h.currentText()
        m = self.target_m.currentText()
        s = self.target_s.currentText()
        return f"{ymd} {h}:{m}:{s}"

    # --- actions ---
    def open_settings(self):
        dlg = SettingsDialog(self.cfg, self)
        dlg.saved.connect(lambda _: self._on_settings_saved())
        dlg.exec()

    def _on_settings_saved(self):
        ConfigManager.save(self.cfg)
        QtWidgets.QMessageBox.information(self, "已保存", "设置已保存。")

    def open_cookie(self):
        """打开Cookie设置对话框，提供手动粘贴和自动登录两种方式"""
        if WEBENGINE_AVAILABLE:
            # 提供选择：自动登录 或 手动粘贴
            choice = QtWidgets.QMessageBox()
            choice.setWindowTitle("设置Cookie")
            choice.setText("请选择Cookie获取方式：")
            choice.setInformativeText(
                "【自动登录】- 推荐！打开浏览器窗口自动登录并捕获\n"
                "【手动粘贴】- 从浏览器开发者工具手动复制Cookie"
            )
            btn_auto = choice.addButton("自动登录", QtWidgets.QMessageBox.YesRole)
            btn_manual = choice.addButton("手动粘贴", QtWidgets.QMessageBox.NoRole)
            choice.addButton(QtWidgets.QMessageBox.Cancel)
            choice.setDefaultButton(btn_auto)

            choice.exec()
            clicked = choice.clickedButton()

            if clicked == btn_auto:
                # 自动登录方式
                self._open_auto_login()
            elif clicked == btn_manual:
                # 手动粘贴方式（原有逻辑）
                self._open_manual_cookie()
        else:
            # 如果 QtWebEngine 不可用，只提供手动粘贴
            self._open_manual_cookie()

    def _open_manual_cookie(self):
        """手动粘贴Cookie与代理"""
        dlg = CookieDialog(self.cfg.cookie, self.cfg.proxies, self)
        def _save_cookie_and_proxy(new_cookie: str, new_proxies: str):
            self.cfg.cookie = new_cookie or ""
            self.cfg.cookie_updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cfg.proxies = new_proxies or ""
            self.cookie_info.setText(self._cookie_summary())
            ConfigManager.save(self.cfg)
        dlg.saved.connect(_save_cookie_and_proxy)
        dlg.exec()

    def _open_auto_login(self):
        """打开自动登录对话框"""
        try:
            dlg = AutoLoginDialog(
                proxies_config=self.cfg.proxies,
                user_id=self.cfg.user_id,
                user_password=self.cfg.user_password,
                parent=self
            )

            def _on_cookie_captured(cookie_str: str):
                self.cfg.cookie = cookie_str
                self.cfg.cookie_updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cookie_info.setText(self._cookie_summary())
                ConfigManager.save(self.cfg)
                QtWidgets.QMessageBox.information(
                    self, "成功",
                    f"已自动捕获Cookie！\n共{len(cookie_str)}个字符\n更新时间：{self.cfg.cookie_updated_at}"
                )

            dlg.cookie_captured.connect(_on_cookie_captured)
            dlg.exec()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "错误",
                f"自动登录功能启动失败：\n{e}\n\n请使用手动粘贴方式。"
            )
            self._open_manual_cookie()

    def _collect_chunks(self) -> List[Tuple[str, str, str]]:
        """
        将 UI 中的每组请求拆分为若干 <= 2h 的片段。
        返回 [(place, 'YYYY-MM-DD HH:MM','YYYY-MM-DD HH:MM'), ...]
        """
        chunks: List[Tuple[str, str, str]] = []
        for w in self._iter_items():
            d = w.to_data()

            # 基础校验
            place = (d.place or "").strip()
            if not place:
                raise ValueError("存在空的地点（place）。")
            # 时间
            s_minutes = hhmm_to_minutes(d.start)
            e_minutes = hhmm_to_minutes(d.end)
            if e_minutes < s_minutes:
                raise ValueError(f"{place} 的结束时间早于开始时间。")

            # 拆分
            for s_hm, e_hm in split_to_slots(d.start, d.end, max_minutes=120):
                start_ts = f"{d.date} {s_hm}"
                end_ts = f"{d.date} {e_hm}"
                chunks.append((place, start_ts, end_ts))
        return chunks

    def _append_log(self, text: str):
        self.te_log.appendPlainText(text)
        self.te_log.verticalScrollBar().setValue(self.te_log.verticalScrollBar().maximum())

    def _set_controls_enabled(self, enabled: bool):
        self.btn_settings.setEnabled(enabled)
        self.btn_cookie.setEnabled(enabled)
        self.btn_add.setEnabled(enabled)
        for w in self._iter_items():
            w.setEnabled(enabled)
        self.target_date.setEnabled(enabled)
        self.target_h.setEnabled(enabled)
        self.target_m.setEnabled(enabled)
        self.target_s.setEnabled(enabled)
        self.cb_immediate.setEnabled(enabled)
        self.btn_start.setEnabled(enabled)

    def _start_worker_now(self):
        # 防重复：若已触发过则直接返回
        if getattr(self, "_has_started", False):
            return
        self._has_started = True

        # 组装 chunks 并启动线程
        try:
            chunks = self._collect_chunks()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "参数错误", str(e))
            self._set_controls_enabled(True)
            return

        # 提示 proxies 解析情况
        proxies = parse_proxies(self.cfg.proxies)
        if self.cfg.proxies and proxies is None:
            QtWidgets.QMessageBox.warning(self, "proxies 格式错误", "请在设置中以 JSON 或 YAML 格式填写 proxies，例如：\n"
                                              '{"http":"10.101.28.225:9000","https":"10.101.28.225:9000"}')
            self._set_controls_enabled(True)
            return

        self._append_log(f"开始执行，共 {len(chunks)} 个片段…")
        self.worker = BookingWorker(self.cfg, chunks)
        self.worker.log.connect(self._append_log)
        self.worker.popup.connect(self._on_popup)
        self.worker.finished_all.connect(self._on_worker_finished)
        self.worker.start()

    def _on_popup(self, level: str, message: str):
        if level == "info":
            QtWidgets.QMessageBox.information(self, "提示", message)
        elif level == "warn":
            QtWidgets.QMessageBox.warning(self, "提示", message)
        else:
            QtWidgets.QMessageBox.critical(self, "错误", message)

    def _on_worker_finished(self):
        self._append_log("所有片段执行完毕。")
        self._set_controls_enabled(True)
        # 允许再次启动
        self._has_started = False

    def on_start_clicked(self):
        # 保存一份配置快照
        self.cfg.target_time = self.current_target_time()
        self.cfg.start_immediately = self.cb_immediate.isChecked()
        ConfigManager.save(self.cfg)

        # 必填校验（设置弹窗里的）
        missing = []
        for key in REQUIRED_FIELDS:
            if not getattr(self.cfg, key):
                missing.append(key)
        if missing:
            QtWidgets.QMessageBox.warning(self, "缺少必填项", '请先在"设置"中填写：' + "、".join(missing))
            return

        # 检查是否配置了密码（用于自动登录）
        if not self.cfg.user_password:
            QtWidgets.QMessageBox.warning(
                self, "缺少密码",
                '请先在"设置"中填写密码，以便自动登录获取Cookie。'
            )
            return

        # 每次运行前自动登录获取Cookie
        if WEBENGINE_AVAILABLE:
            self._append_log("正在自动登录获取Cookie...")
            self._auto_login_and_start()
        else:
            # 如果 WebEngine 不可用，检查是否有Cookie
            if not self.cfg.cookie:
                if QtWidgets.QMessageBox.question(
                    self, "未设置Cookie", '尚未设置 Cookie，是否继续？（可能导致"Cookie 过期"）',
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                ) == QtWidgets.QMessageBox.No:
                    return
            self._set_controls_enabled(False)
            self._schedule_start()

    def _auto_login_and_start(self):
        """自动登录获取Cookie，然后开始预定"""
        try:
            dlg = AutoLoginDialog(
                proxies_config=self.cfg.proxies,
                user_id=self.cfg.user_id,
                user_password=self.cfg.user_password,
                parent=self
            )

            def _on_cookie_captured(cookie_str: str):
                self.cfg.cookie = cookie_str
                self.cfg.cookie_updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cookie_info.setText(self._cookie_summary())
                ConfigManager.save(self.cfg)
                self._append_log(f"Cookie获取成功！更新时间：{self.cfg.cookie_updated_at}")

                # Cookie获取成功后，继续预定流程
                self._set_controls_enabled(False)
                self._schedule_start()

            def _on_rejected():
                self._append_log("用户取消了自动登录。")
                QtWidgets.QMessageBox.information(
                    self, "已取消",
                    '已取消自动登录。如需继续，请重新点击"开始"按钮。'
                )

            dlg.cookie_captured.connect(_on_cookie_captured)
            dlg.rejected.connect(_on_rejected)
            dlg.exec()

        except Exception as e:
            self._append_log(f"自动登录失败：{e}")
            QtWidgets.QMessageBox.critical(
                self, "自动登录失败",
                f"自动登录功能启动失败：\n{e}\n\n请检查网络连接或代理设置。"
            )

    def _schedule_start(self):
        """调度启动预定任务（立即或定时）"""
        if self.cb_immediate.isChecked():
            self._append_log('"立即启动"已勾选，马上开始…')
            self._start_worker_now()
        else:
            # 使用 Qt 定时器保证触发，并保留核心 timer_run 作为后备
            target = self.current_target_time()
            self._append_log(f"已预约在 {target} 启动…（窗口保持打开即可）")

            # 计算延迟
            try:
                run_dt = datetime.strptime(target, "%Y-%m-%d %H:%M:%S")
                delay_ms = int(max(0, (run_dt - datetime.now()).total_seconds()) * 1000)
            except Exception:
                delay_ms = 0

            if delay_ms == 0:
                self._append_log("目标时间已到或已过，立即开始…")
                self._start_worker_now()
                return

            # 主调度：Qt 单次定时器
            if self.qt_timer is not None:
                try:
                    self.qt_timer.stop()
                except Exception:
                    pass
                try:
                    self.qt_timer.deleteLater()
                except Exception:
                    pass
                self.qt_timer = None
            self._has_started = False
            self.qt_timer = QtCore.QTimer(self)
            self.qt_timer.setSingleShot(True)
            self.qt_timer.timeout.connect(self._start_worker_now)
            self.qt_timer.start(delay_ms)

            # 后备：仍调用用户核心 timer_run（若触发也会因为 _has_started 防重）
            def _go():
                QtCore.QTimer.singleShot(0, self._start_worker_now)
            try:
                self.scheduled_timer = timer_run(target, _go)
            except Exception:
                self.scheduled_timer = None

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
