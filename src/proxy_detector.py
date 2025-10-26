# -*- coding: utf-8 -*-
"""
智能代理检测模块
自动检测并配置可用的代理，无需手动输入
"""

import winreg
import socket
import requests
from typing import Optional, Dict, List, Tuple


class ProxyDetector:
    """智能代理检测器"""

    # 常见代理软件的默认端口
    COMMON_PROXY_PORTS = [
        ("Reqable", 9000),
        ("Reqable", 9001),  # Reqable 可选端口
        ("Reqable", 9002),  # Reqable 可选端口
        ("Reqable", 8080),  # Reqable HTTP 端口
        ("Reqable", 9443),  # Reqable HTTPS 端口
        ("Clash", 7890),
        ("V2Ray", 10809),
        ("SSR", 1080),
        ("Fiddler", 8888),
        ("Charles", 8888),
    ]

    # 测试用的学校网站URL
    TEST_URLS = [
        "https://booking.cuhk.edu.cn",
        "https://sts.cuhk.edu.cn",
    ]

    @staticmethod
    def is_anyconnect_connected() -> bool:
        """
        检测Cisco AnyConnect VPN是否已连接
        通过检查进程和网络适配器来判断
        """
        import subprocess
        import re

        try:
            # 方法1：检查AnyConnect进程是否在运行
            tasklist_output = subprocess.check_output("tasklist", shell=True).decode('gbk', errors='ignore')
            if "vpnagent.exe" in tasklist_output.lower() or "vpnui.exe" in tasklist_output.lower():
                print("[ProxyDetector] 检测到 AnyConnect 进程正在运行")

                # 方法2：检查是否有Cisco虚拟适配器
                try:
                    ipconfig_output = subprocess.check_output("ipconfig /all", shell=True).decode('gbk', errors='ignore')
                    # 查找Cisco AnyConnect虚拟适配器
                    if "cisco anyconnect" in ipconfig_output.lower() or "vpn" in ipconfig_output.lower():
                        # 检查是否有IP地址分配（表示已连接）
                        lines = ipconfig_output.split('\n')
                        in_cisco_adapter = False
                        for line in lines:
                            if "cisco anyconnect" in line.lower() or "vpn" in line.lower():
                                in_cisco_adapter = True
                            elif in_cisco_adapter and "ipv4" in line.lower():
                                # 找到了IP地址
                                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                                if match and match.group(1) != "0.0.0.0":
                                    print(f"[ProxyDetector] AnyConnect 已连接，VPN IP: {match.group(1)}")
                                    return True
                            elif line.strip() and not line.startswith(' '):
                                in_cisco_adapter = False

                except Exception as e:
                    print(f"[ProxyDetector] 检查网络适配器失败: {e}")

        except Exception as e:
            print(f"[ProxyDetector] 检测 AnyConnect 失败: {e}")

        return False

    @staticmethod
    def test_direct_connection(timeout: float = 5.0) -> bool:
        """
        测试不使用代理直接连接学校网站
        专为 AnyConnect VPN 和校园网内连接优化
        """
        print("[ProxyDetector] 测试直接连接（不使用代理）...")

        # 先尝试使用系统证书（正常情况）
        print("[ProxyDetector] 尝试使用系统证书进行直接连接...")
        for url in ProxyDetector.TEST_URLS:
            try:
                # 创建自定义session
                session = requests.Session()

                # 设置User-Agent（模拟浏览器）
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                })

                # 禁用环境变量中的代理设置（这是关键！）
                session.trust_env = False

                response = session.get(
                    url,
                    proxies={"http": None, "https": None},  # 明确禁用代理
                    timeout=timeout,
                    verify=True,  # 启用SSL验证
                    allow_redirects=True
                )

                if response.status_code in (200, 302, 401, 403):
                    print(f"[ProxyDetector] [OK] 直接连接成功！访问 {url} (状态码: {response.status_code})")
                    return True

            except requests.exceptions.SSLError as e:
                # SSL 错误可能是因为 AnyConnect 的中间人证书问题
                print(f"[ProxyDetector] SSL错误: {str(e)[:100]}...")
                print("[ProxyDetector] 尝试禁用SSL验证重试...")

                # 重试，禁用SSL验证（某些 VPN 配置可能需要）
                try:
                    session = requests.Session()
                    session.headers.update({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    })
                    session.trust_env = False

                    response = session.get(
                        url,
                        proxies={"http": None, "https": None},
                        timeout=timeout,
                        verify=False,  # 禁用SSL验证
                        allow_redirects=True
                    )

                    if response.status_code in (200, 302, 401, 403):
                        print(f"[ProxyDetector] [OK] 直接连接成功（禁用SSL验证）！访问 {url} (状态码: {response.status_code})")
                        return True

                except Exception as retry_e:
                    print(f"[ProxyDetector] 重试失败: {str(retry_e)[:100]}...")
                    continue

            except requests.exceptions.ConnectionError as e:
                print(f"[ProxyDetector] 连接错误: {str(e)[:100]}...")
                continue
            except requests.exceptions.Timeout as e:
                print(f"[ProxyDetector] 超时: {str(e)[:100]}...")
                continue
            except Exception as e:
                print(f"[ProxyDetector] 其他错误: {str(e)[:100]}...")
                continue

        print("[ProxyDetector] [FAIL] 无法直接连接到学校网站")
        return False

    @staticmethod
    def get_system_proxy() -> Optional[Dict[str, str]]:
        """
        从Windows注册表读取系统代理设置
        返回格式：{"http": "127.0.0.1:9000", "https": "127.0.0.1:9000"} 或 None
        """
        try:
            # 打开注册表项
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0,
                winreg.KEY_READ
            )

            # 检查是否启用代理
            proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
            if not proxy_enable:
                winreg.CloseKey(key)
                return None

            # 读取代理服务器地址
            proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
            winreg.CloseKey(key)

            if not proxy_server:
                return None

            # 解析代理地址
            # 格式1: "127.0.0.1:9000"
            # 格式2: "http=127.0.0.1:9000;https=127.0.0.1:9000"
            if "=" in proxy_server:
                # 多协议代理
                proxies = {}
                for part in proxy_server.split(";"):
                    if "=" in part:
                        protocol, addr = part.split("=", 1)
                        proxies[protocol.strip()] = f"http://{addr.strip()}"
                return proxies if proxies else None
            else:
                # 单一代理地址
                return {
                    "http": f"http://{proxy_server}",
                    "https": f"http://{proxy_server}"
                }

        except Exception as e:
            print(f"[ProxyDetector] 读取系统代理失败: {e}")
            return None

    @staticmethod
    def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
        """
        检测指定端口是否开放（有程序监听）
        """
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            return result == 0
        except Exception:
            return False
        finally:
            if sock:
                sock.close()

    @staticmethod
    def test_proxy(proxy_dict: Dict[str, str], timeout: float = 5.0) -> bool:
        """
        测试代理是否能访问学校网站
        """
        for url in ProxyDetector.TEST_URLS:
            try:
                response = requests.get(
                    url,
                    proxies=proxy_dict,
                    timeout=timeout,
                    verify=False  # 忽略SSL证书验证
                )
                if response.status_code in (200, 302, 401, 403):
                    # 200: 正常访问
                    # 302: 重定向（可能到登录页）
                    # 401/403: 需要认证（说明能连接到服务器）
                    print(f"[ProxyDetector] [OK] 代理可用，成功访问 {url}")
                    return True
            except requests.exceptions.ProxyError:
                print(f"[ProxyDetector] [FAIL] 代理错误，无法连接到代理服务器")
                return False
            except requests.exceptions.Timeout:
                print(f"[ProxyDetector] [FAIL] 超时，代理可能不稳定")
                continue
            except Exception as e:
                print(f"[ProxyDetector] [FAIL] 测试失败: {e}")
                continue

        return False

    @staticmethod
    def detect_local_proxies() -> List[Tuple[str, int]]:
        """
        检测本地正在运行的代理软件
        返回：[(软件名, 端口)]
        """
        available = []
        for name, port in ProxyDetector.COMMON_PROXY_PORTS:
            if ProxyDetector.is_port_open("127.0.0.1", port, timeout=0.5):
                print(f"[ProxyDetector] 检测到 {name} 正在运行（端口 {port}）")
                available.append((name, port))
        return available

    @staticmethod
    def auto_detect() -> Optional[Dict[str, str]]:
        """
        自动检测可用的网络配置

        优先级（已针对 booking.cuhk.edu.cn 的 SSL 问题优化）：
        1. 本地代理软件（Reqable）- 优先检测，因为 booking 接口需要通过 Reqable
        2. 直接连接测试（校园网内或 AnyConnect VPN）- 仅当 Reqable 未运行时使用
        3. 系统代理设置

        返回格式：
        - None: 表示使用直接连接（不使用代理）
        - {"http": "127.0.0.1:9000", "https": "127.0.0.1:9000"}: 使用代理

        注意：由于 booking.cuhk.edu.cn 的 SSL 配置特殊，Python requests 库无法
        直接连接（即使通过 VPN），因此优先检测 Reqable 代理。
        """
        print("[ProxyDetector] 开始自动检测网络配置...")
        print("[ProxyDetector] 注意：booking接口需要Reqable代理才能正常工作")

        # 步骤1：优先检测本地代理软件（Reqable）
        print("[ProxyDetector] 步骤1：检测本地代理软件（Reqable等）...")
        local_proxies = ProxyDetector.detect_local_proxies()

        if local_proxies:
            print(f"[ProxyDetector] 找到 {len(local_proxies)} 个代理软件")
            # 逐个测试本地代理
            for name, port in local_proxies:
                proxy_dict = {
                    "http": f"http://127.0.0.1:{port}",
                    "https": f"http://127.0.0.1:{port}"
                }
                print(f"[ProxyDetector] 测试 {name} (127.0.0.1:{port})...")
                if ProxyDetector.test_proxy(proxy_dict, timeout=3):
                    print(f"[ProxyDetector] [OK] 找到可用代理: {name} (127.0.0.1:{port})")
                    print(f"[ProxyDetector] 建议：使用 {name} 代理进行预订")
                    return proxy_dict
                else:
                    print(f"[ProxyDetector] [FAIL] {name} 代理无法访问学校网站")
        else:
            print("[ProxyDetector] 未检测到 Reqable 等代理软件正在运行")

        # 步骤2：测试直接连接（校园网内或 AnyConnect VPN）
        print("[ProxyDetector] 步骤2：测试直接连接（校园网内或VPN）...")
        if ProxyDetector.test_direct_connection(timeout=5):
            print("[ProxyDetector] [OK] 可以直接连接到学校网站！")

            # 检测是否通过 AnyConnect VPN 连接
            if ProxyDetector.is_anyconnect_connected():
                print("[ProxyDetector] 检测到 AnyConnect VPN 已连接")
                print("[ProxyDetector] [WARNING] 警告：即使VPN可访问，booking接口仍可能需要Reqable")
                print("[ProxyDetector] 建议：如果预订失败，请启动Reqable并重新检测")
            else:
                print("[ProxyDetector] 可能在校园网内，可以直接访问")
                print("[ProxyDetector] 建议：如果预订失败，请启动Reqable并重新检测")

            return None  # 返回 None 表示不使用代理

        # 如果直接连接失败，检查是否有 AnyConnect 进程但未连接
        print("[ProxyDetector] 直接连接失败，检查 AnyConnect 状态...")
        if ProxyDetector.is_anyconnect_connected():
            print("[ProxyDetector] [WARNING] AnyConnect 进程在运行但无法访问学校网站")
            print("[ProxyDetector] 可能原因：VPN 未完全建立或网络不稳定")
            print("[ProxyDetector] 建议：检查 AnyConnect 连接状态，或启动 Reqable")

        # 步骤3：检测系统代理
        print("[ProxyDetector] 步骤3：检查系统代理设置...")
        sys_proxy = ProxyDetector.get_system_proxy()
        if sys_proxy:
            print(f"[ProxyDetector] 找到系统代理: {sys_proxy}")
            if ProxyDetector.test_proxy(sys_proxy, timeout=3):
                print("[ProxyDetector] [OK] 系统代理可用！")
                return sys_proxy
            else:
                print("[ProxyDetector] [FAIL] 系统代理无法访问学校网站")

        # 所有方法都失败
        print("[ProxyDetector] [FAIL] 所有检测方法都无法访问学校网站")
        print("[ProxyDetector] 建议：")
        print("  1. 启动 Reqable 代理软件（推荐，解决booking接口SSL问题）")
        print("  2. 连接 AnyConnect VPN（可用于自动登录，但预订可能需要Reqable）")
        print("  3. 或在校园网内使用")
        return None

    @staticmethod
    def format_for_config(proxy_dict: Optional[Dict[str, str]]) -> str:
        """
        将代理字典格式化为配置文件中的字符串
        例如：{"http": "http://127.0.0.1:9000", "https": "http://127.0.0.1:9000"}
        转换为："127.0.0.1:9000"

        如果 proxy_dict 为 None，返回空字符串（表示直接连接）
        """
        if not proxy_dict:
            return ""

        # 提取地址（去掉 http:// 前缀）
        http_proxy = proxy_dict.get("http", "")
        if http_proxy.startswith("http://"):
            return http_proxy[7:]  # 去掉 "http://"
        return http_proxy


def test_proxy_detector():
    """测试代理检测功能"""
    print("=" * 60)
    print("智能代理检测测试")
    print("=" * 60)

    detector = ProxyDetector()
    proxy = detector.auto_detect()

    if proxy:
        print("\n" + "=" * 60)
        print("[OK] 检测成功！")
        print("=" * 60)
        print(f"代理配置: {proxy}")
        print(f"配置文件格式: {detector.format_for_config(proxy)}")
    else:
        print("\n" + "=" * 60)
        print("[FAIL] 未找到可用代理")
        print("=" * 60)


if __name__ == "__main__":
    # 禁用SSL警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    test_proxy_detector()
