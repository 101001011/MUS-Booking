# -*- coding: utf-8 -*-
"""
Dialogs package
从 GUI.py 提取的对话框
"""

from .settings_dialog import SettingsDialog
from .cookie_dialog import CookieDialog
from .auto_login_dialog import AutoLoginDialog

__all__ = [
    'SettingsDialog',
    'CookieDialog',
    'AutoLoginDialog'
]
