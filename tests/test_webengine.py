# -*- coding: utf-8 -*-
"""
测试 QtWebEngine 是否可用
"""

import sys

try:
    from PySide6.QtCore import QUrl
    from PySide6.QtWidgets import QApplication
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineProfile

    print("[OK] QtWebEngine modules imported successfully!")

    # 创建应用测试
    app = QApplication(sys.argv)

    # 创建 WebEngineView
    view = QWebEngineView()
    view.setWindowTitle("QtWebEngine Test")
    view.resize(1024, 768)

    # 加载测试页面
    view.setUrl(QUrl("https://www.baidu.com"))
    view.show()

    print("[OK] QtWebEngineView created successfully!")
    print("[OK] Browser window opened. Press Ctrl+C to close.")
    print("\nIf you can see Baidu homepage, QtWebEngine is working properly.")

    sys.exit(app.exec())

except ImportError as e:
    print("[ERROR] QtWebEngine module import failed!")
    print(f"Error message: {e}")
    print("\nPlease install PySide6-WebEngine:")
    print("  pip install PySide6-WebEngine")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] An error occurred: {e}")
    sys.exit(1)
