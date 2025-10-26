# -*- coding: utf-8 -*-
"""
测试网络连接的不同模式
验证 CrazyRequests 类的改进
"""

import sys
from main import CrazyRequests

# 禁用 SSL 警告
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass

TEST_URLS = [
    "https://booking.cuhk.edu.cn",
    "https://sts.cuhk.edu.cn",
]


def test_direct_connection():
    """测试直接连接（不使用代理）"""
    print("=" * 60)
    print("测试 1: 直接连接（proxies=None）")
    print("=" * 60)

    requester = CrazyRequests(proxies=None, cookie="")

    for url in TEST_URLS:
        try:
            response = requester.get(url)
            print(f"[OK] {url}")
            print(f"    状态码: {response.status_code}")
            print(f"    响应长度: {len(response.content)} bytes")
        except Exception as e:
            print(f"[FAIL] {url}")
            print(f"    错误: {type(e).__name__}: {str(e)[:100]}")
    print()


def test_empty_dict_connection():
    """测试空字典代理（相当于直接连接）"""
    print("=" * 60)
    print("测试 2: 空字典代理（proxies={}）")
    print("=" * 60)

    requester = CrazyRequests(proxies={}, cookie="")

    for url in TEST_URLS:
        try:
            response = requester.get(url)
            print(f"[OK] {url}")
            print(f"    状态码: {response.status_code}")
            print(f"    响应长度: {len(response.content)} bytes")
        except Exception as e:
            print(f"[FAIL] {url}")
            print(f"    错误: {type(e).__name__}: {str(e)[:100]}")
    print()


def test_proxy_connection():
    """测试使用代理连接"""
    print("=" * 60)
    print("测试 3: 使用代理（proxies={'http': '127.0.0.1:9000', ...}）")
    print("=" * 60)

    proxies = {
        "http": "http://127.0.0.1:9000",
        "https": "http://127.0.0.1:9000"
    }

    requester = CrazyRequests(proxies=proxies, cookie="")

    for url in TEST_URLS:
        try:
            response = requester.get(url)
            print(f"[OK] {url}")
            print(f"    状态码: {response.status_code}")
            print(f"    响应长度: {len(response.content)} bytes")
        except Exception as e:
            print(f"[FAIL] {url}")
            print(f"    错误: {type(e).__name__}: {str(e)[:100]}")
    print()


def main():
    print("\n" + "=" * 60)
    print("CrazyRequests 连接测试")
    print("=" * 60)
    print()

    # 测试 1: 直接连接
    test_direct_connection()

    # 测试 2: 空字典（也是直接连接）
    test_empty_dict_connection()

    # 测试 3: 使用代理
    test_proxy_connection()

    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
