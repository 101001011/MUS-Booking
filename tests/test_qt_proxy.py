# -*- coding: utf-8 -*-
"""
测试 QWebEngineView 的代理设置
"""

from PySide6 import QtWidgets, QtCore, QtNetwork
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
import sys


def test_no_proxy():
    """测试设置 NoProxy"""
    print("=" * 60)
    print("测试 1: 设置 NoProxy（直接连接）")
    print("=" * 60)

    # 创建 QNetworkProxy 并设置为 NoProxy
    proxy = QtNetwork.QNetworkProxy()
    proxy.setType(QtNetwork.QNetworkProxy.NoProxy)
    QtNetwork.QNetworkProxy.setApplicationProxy(proxy)

    print("[OK] 已设置 NoProxy")

    # 查询当前代理
    current_proxy = QtNetwork.QNetworkProxy.applicationProxy()
    print(f"当前代理类型: {current_proxy.type()}")
    print(f"  - NoProxy = {QtNetwork.QNetworkProxy.NoProxy}")
    print(f"  - HttpProxy = {QtNetwork.QNetworkProxy.HttpProxy}")

    if current_proxy.type() == QtNetwork.QNetworkProxy.NoProxy:
        print("[OK] 验证成功：当前为直接连接模式")
    else:
        print("[FAIL] 验证失败：代理设置未生效")

    print()


def test_http_proxy():
    """测试设置 HTTP 代理"""
    print("=" * 60)
    print("测试 2: 设置 HTTP 代理（127.0.0.1:9000）")
    print("=" * 60)

    proxy = QtNetwork.QNetworkProxy()
    proxy.setType(QtNetwork.QNetworkProxy.HttpProxy)
    proxy.setHostName("127.0.0.1")
    proxy.setPort(9000)
    QtNetwork.QNetworkProxy.setApplicationProxy(proxy)

    print("[OK] 已设置 HTTP 代理")

    # 查询当前代理
    current_proxy = QtNetwork.QNetworkProxy.applicationProxy()
    print(f"当前代理类型: {current_proxy.type()}")
    print(f"主机名: {current_proxy.hostName()}")
    print(f"端口: {current_proxy.port()}")

    if current_proxy.type() == QtNetwork.QNetworkProxy.HttpProxy:
        print("[OK] 验证成功：代理设置已生效")
    else:
        print("[FAIL] 验证失败：代理设置未生效")

    print()


def test_webengine_with_no_proxy():
    """测试 WebEngineView 在 NoProxy 模式下的表现"""
    print("=" * 60)
    print("测试 3: WebEngineView 在 NoProxy 模式下访问学校网站")
    print("=" * 60)

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    # 设置 NoProxy
    proxy = QtNetwork.QNetworkProxy()
    proxy.setType(QtNetwork.QNetworkProxy.NoProxy)
    QtNetwork.QNetworkProxy.setApplicationProxy(proxy)
    print("[OK] 已设置 NoProxy")

    # 创建 WebEngineView
    window = QtWidgets.QMainWindow()
    browser = QWebEngineView()
    window.setCentralWidget(browser)
    window.setWindowTitle("测试 WebEngineView - NoProxy 模式")
    window.resize(1024, 768)

    # 加载学校网站
    test_url = "https://sts.cuhk.edu.cn"
    print(f"正在加载: {test_url}")

    def on_load_finished(success):
        if success:
            print(f"[OK] 页面加载成功！")
            print(f"最终 URL: {browser.url().toString()}")
        else:
            print(f"[FAIL] 页面加载失败")
            print(f"当前 URL: {browser.url().toString()}")

        # 5秒后自动关闭
        QtCore.QTimer.singleShot(5000, app.quit)

    browser.loadFinished.connect(on_load_finished)
    browser.load(test_url)

    window.show()
    app.exec()
    print()


def main():
    print("\n" + "=" * 60)
    print("QNetworkProxy 代理设置测试")
    print("=" * 60)
    print()

    # 测试 1 和 2：基本代理设置
    test_no_proxy()
    test_http_proxy()

    # 测试 3：WebEngineView（需要 GUI）
    print("注意：测试 3 需要手动运行")
    print("运行命令：python test_qt_proxy.py --webengine")
    print()

    if "--webengine" in sys.argv:
        test_webengine_with_no_proxy()


if __name__ == "__main__":
    main()
