# -*- coding: utf-8 -*-
"""
详细检查 SSL 连接问题
"""

import requests
import ssl

# 禁用 SSL 警告
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass

TEST_URL = "https://booking.cuhk.edu.cn"


def test_with_verify():
    """使用 SSL 验证"""
    print("测试 1: verify=True（启用 SSL 验证）")
    session = requests.Session()
    session.trust_env = False

    try:
        response = session.get(
            TEST_URL,
            proxies={"http": None, "https": None},
            verify=True,
            timeout=10
        )
        print(f"[OK] 状态码: {response.status_code}")
    except requests.exceptions.SSLError as e:
        print(f"[FAIL] SSL 错误")
        print(f"详细信息: {e}")
    except Exception as e:
        print(f"[FAIL] 其他错误: {type(e).__name__}: {e}")
    print()


def test_without_verify():
    """禁用 SSL 验证"""
    print("测试 2: verify=False（禁用 SSL 验证）")
    session = requests.Session()
    session.trust_env = False

    try:
        response = session.get(
            TEST_URL,
            proxies={"http": None, "https": None},
            verify=False,
            timeout=10
        )
        print(f"[OK] 状态码: {response.status_code}")
        print(f"响应长度: {len(response.content)} bytes")
    except Exception as e:
        print(f"[FAIL] 错误: {type(e).__name__}: {e}")
    print()


def main():
    print("=" * 60)
    print("SSL 连接详细测试")
    print(f"目标 URL: {TEST_URL}")
    print("=" * 60)
    print()

    test_with_verify()
    test_without_verify()

    print("=" * 60)
    print("结论:")
    print("如果测试2成功，说明是 SSL 证书验证问题")
    print("可能原因：AnyConnect 使用了自签名证书")
    print("=" * 60)


if __name__ == "__main__":
    main()
