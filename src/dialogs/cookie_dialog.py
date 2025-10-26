# -*- coding: utf-8 -*-
"""
CookieDialog对话框
从 GUI.py 提取的模块
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

from PySide6 import QtCore, QtGui, QtWidgets

# 导入工具函数
from utils import parse_proxies

# 导入代理检测模块
try:
    from proxy_detector import ProxyDetector
    PROXY_DETECTOR_AVAILABLE = True
except ImportError:
    PROXY_DETECTOR_AVAILABLE = False


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
