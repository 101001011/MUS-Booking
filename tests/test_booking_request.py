# -*- coding: utf-8 -*-
"""
测试预订请求的网络连接
"""

import sys
from main import CrazyRequests

# 禁用 SSL 警告
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass


def test_booking_endpoint():
    """测试预订接口的连接"""
    print("=" * 60)
    print("测试预订接口连接")
    print("=" * 60)

    # 预订接口
    url = "https://booking.cuhk.edu.cn/a/field/book/bizFieldBookMain/saveData"

    # 测试参数
    params = {"reBookMainId": "", "ruleId": "4b4d6e5c826c425b9a5ed7a02a46656a"}

    # 简单的测试数据（不会真正预订，因为没有有效的Cookie）
    data = {
        "id": "test",
        "user.id": "test",
        "bizFieldBookField.FId": "test",
    }

    print("\n测试 1: 不使用代理（proxies=None）")
    print("-" * 60)

    try:
        requester = CrazyRequests(proxies=None, cookie="")
        print("[OK] CrazyRequests 对象创建成功")
        print(f"use_proxy: {requester.use_proxy}")
        print(f"session.trust_env: {requester.session.trust_env}")

        print(f"\n正在发送 POST 请求到: {url}")
        response = requester.post(url, params=params, data=data)

        print(f"[OK] 请求成功！")
        print(f"状态码: {response.status_code}")
        print(f"响应长度: {len(response.content)} bytes")

        # 尝试解析响应
        try:
            json_response = response.json()
            print(f"响应内容: {json_response}")
        except:
            print(f"响应文本（前200字符）: {response.text[:200]}")

    except Exception as e:
        print(f"[FAIL] 请求失败")
        print(f"异常类型: {type(e).__name__}")
        print(f"异常信息: {e}")

        # 打印详细的异常信息
        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()

    print("\n" + "=" * 60)


def test_simple_connection():
    """测试简单的GET请求"""
    print("\n测试 2: 简单GET请求")
    print("-" * 60)

    test_url = "https://booking.cuhk.edu.cn"

    try:
        requester = CrazyRequests(proxies=None, cookie="")
        print(f"正在访问: {test_url}")

        response = requester.get(test_url)
        print(f"[OK] 请求成功！")
        print(f"状态码: {response.status_code}")
        print(f"响应长度: {len(response.content)} bytes")

    except Exception as e:
        print(f"[FAIL] 请求失败")
        print(f"异常类型: {type(e).__name__}")
        print(f"异常信息: {e}")

        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()


def main():
    print("\n" + "=" * 60)
    print("预订请求网络诊断")
    print("=" * 60)
    print()

    # 测试简单连接
    test_simple_connection()

    # 测试预订接口
    test_booking_endpoint()

    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
