import uuid
import threading
from datetime import datetime
import requests


class CrazyRequests:

    def __init__(self, proxies: dict | None = None, cookie: str = ""):
        # 处理代理配置
        # None 或空字典 {} 表示直接连接（不使用任何代理）
        # 非空字典表示使用指定的代理
        self.proxies = proxies
        self.use_proxy = proxies is not None and len(proxies) > 0

        # 创建 session 以便更好地控制连接行为
        self.session = requests.Session()
        self.session.headers.update({
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
        })

        # 如果不使用代理，禁用环境变量检测，确保直接连接
        if not self.use_proxy:
            self.session.trust_env = False  # 忽略环境变量中的代理设置

    def get(self, url, params: dict | None = None):
        # 直接连接时，先尝试启用 SSL 验证，如果失败则尝试禁用
        if not self.use_proxy:
            # 尝试1：启用SSL验证
            try:
                return self.session.get(
                    url,
                    params=params,
                    proxies={"http": None, "https": None},
                    verify=True,
                    timeout=10,
                )
            except requests.exceptions.SSLError as ssl_err:
                # SSL 错误，尝试禁用验证
                print(f"[CrazyRequests] SSL验证失败，尝试禁用验证: {str(ssl_err)[:100]}")
                try:
                    return self.session.get(
                        url,
                        params=params,
                        proxies={"http": None, "https": None},
                        verify=False,
                        timeout=10,
                    )
                except Exception as e:
                    # 禁用验证仍然失败，可能是SSL握手问题，抛出详细错误
                    print(f"[CrazyRequests] 禁用SSL验证后仍然失败: {type(e).__name__}: {e}")
                    raise IOError(f"无法连接到服务器（SSL握手失败）。请尝试使用代理（Reqable）。详细错误: {e}")
        else:
            # 使用代理时直接禁用 SSL 验证
            return self.session.get(
                url,
                params=params,
                proxies=self.proxies,
                verify=False,
                timeout=10,
            )

    def post(
        self,
        url,
        params: dict | None = None,
        data: dict | None = None,
        json: dict | None = None,
    ):
        # 直接连接时，先尝试启用 SSL 验证，如果失败则尝试禁用
        if not self.use_proxy:
            # 尝试1：启用SSL验证
            try:
                return self.session.post(
                    url,
                    params=params,
                    data=data,
                    json=json,
                    proxies={"http": None, "https": None},
                    verify=True,
                    timeout=10,
                )
            except requests.exceptions.SSLError as ssl_err:
                # SSL 错误，尝试禁用验证
                print(f"[CrazyRequests] SSL验证失败，尝试禁用验证: {str(ssl_err)[:100]}")
                try:
                    return self.session.post(
                        url,
                        params=params,
                        data=data,
                        json=json,
                        proxies={"http": None, "https": None},
                        verify=False,
                        timeout=10,
                    )
                except Exception as e:
                    # 禁用验证仍然失败，可能是SSL握手问题，抛出详细错误
                    print(f"[CrazyRequests] 禁用SSL验证后仍然失败: {type(e).__name__}: {e}")
                    raise IOError(f"无法连接到服务器（SSL握手失败）。请尝试使用代理（Reqable）。详细错误: {e}")
        else:
            # 使用代理时直接禁用 SSL 验证
            return self.session.post(
                url,
                params=params,
                data=data,
                json=json,
                proxies=self.proxies,
                verify=False,
                timeout=10,
            )


def book(
    cookie: str,
    user_id: str,
    user_name: str,
    place: str,
    start_time: str,
    end_time: str,
    user_email: str = "example@link.cuhk.edu.cn",
    user_phone: str = "123456",
    theme: str = "练琴",
    proxies: dict | None = None,
) -> str:
    """预定

    Args:
        user_id (str): 学号
        user_name (str): 姓名
        user_email (str): 邮箱
        user_phone (str): 电话
        theme (str): 预定主题
        place (str): 预定地点, 必须是 FID_MAP 的 key 之一
        start_time (str): 开始时间, 格式 "2025-09-12 18:30"
        end_time (str): 结束时间, 格式 "2025-09-12 19:00"

    returns:
        str: 预定结果
    """
    EXTEND1 = "af15efadc379429885681cbad7b1ec12"
    RULE_ID = "4b4d6e5c826c425b9a5ed7a02a46656a"

    FID_MAP = {
        "MPC319 管弦乐学部": "0bf599e78f3a46dda05e65cd8fd4f61a",
        "MPC320 管弦乐学部": "117da0ca23dd4ff4860dff461e9d6ff4",
        "MPC321 室内乐琴房（GP）": "76e34000bc5348598a705ae483005308",
        "MPC322 室内乐琴房（UP）": "f02f83d544f4490f8237c869eee87913",
        "MPC323 管弦乐学部琴房": "a73c09fc1dd74ee7a495edae53b7c2f0",
        "MPC324 管弦乐学部琴房": "62508f2d7a91455fad00839609b1c63b",
        "MPC325 管弦乐学部琴房（UP）": "28209733f1be415383f16a253737f2db",
        "MPC326 管弦乐学部琴房（UP）": "af3b514fb3f5490ead315a4152df6abd",
        "MPC327 管弦乐学部琴房（UP）": "34d88aa5f4fd476ab013dcc561ee1063",
        "MPC328 管弦乐学部琴房（UP）": "1ab85f1a6dc44474ae8bad97a55097e9",
        "MPC329 管弦乐学部琴房（UP）": "d828d19e79604c3cb02040576bd23104",
        "MPC334 室内乐琴房（GP）": "dc4f0f555ac34e5e8c659b71887e9743",
        "MPC335 管弦乐学部琴房": "2a695052a7ce4d11aa0e23b96194ec32",
        "MPC336 管弦乐学部琴房": "032bba7d83ff4a20a4ab74f9343f3b82",
        "MPC337 管弦乐学部琴房": "7c410dcf1a1747d2b3e35d1e16b9894e",
        "MPC401 管弦乐学部琴房": "b67000e23c27464386ee417d3851aa00",
        "MPC402 管弦乐学部琴房": "f69d6cf620d149e2bc1800a2c61d1843",
        "MPC403 管弦乐学部琴房": "e5cd05208c7343148050fbc54c9df753",
        "MPC404 管弦乐学部琴房": "07b0c915577049e786ce4608b419a56f",
        "MPC405 管弦乐学部琴房": "ce111f3b2d5e481abd10ed03d15dc282",
        "MPC406 管弦乐学部琴房（UP）": "eec8bb6419c04d3581264b1497f70248",
        "MPC407 管弦乐学部琴房": "2f446f29b3cf456aac29d260b883380d",
        "MPC408 管弦乐学部琴房（UP）": "9aac575aab0b4c76a7b5e009d745eadd",
        "MPC409 管弦乐学部琴房（UP）": "8d84d1b18a6141cdbf2513b4bdfe68ba",
        "MPC410 管弦乐学部琴房": "5da100f8db6f449c97ba445c0bfe8eb6",
        "MPC411 管弦乐学部琴房": "fda92551c763443abc5e0c189295512c",
        "MPC412 室内乐琴房（GP）": "1c89c2dacef342e7be2b37c98c275236",
        "MPC413 室内乐琴房（UP）": "da7a15b42471405bb0af3bfa5e7f7238",
        "MPC414 管弦乐学部琴房": "c3327b0749e545d7b64516a682e18189",
        "MPC415 管弦乐学部琴房（UP）": "6d782a5fe1054a32bb6ae4b135648593",
        "MPC416 管弦乐学部琴房": "68e84f84eee1461a8e9dfe9ed5b4c5b1",
        "MPC417 管弦乐学部琴房（UP）": "a2cf5f7eea204adabb1b644f99e1d9bc",
        "MPC418 管弦乐学部琴房（GP）": "55590a8d83f84744bb11634fc2d7738e",
        "MPC419 管弦乐学部琴房（GP）": "b2892c0e12f94b4ca36a3618bd33628c",
        "MPC420 管弦乐学部琴房（GP）": "0cbb5a428d484333b52f904e534444af",
        "MPC421 管弦乐学部琴房": "d15552be0d9849eb8549d1a63b2e862e",
        "MPC422 管弦乐学部琴房（GP）": "bb9b779bf79c416c905149dd21e47bc4",
        "MPC423 管弦乐学部琴房": "b36918432d2246859761f7e0c0eb147b",
        "MPC424 管弦乐学部琴房（GP）": "0041a2034f7348e7a2a5cd279c5d5d93",
        "MPC425 室内乐琴房（GP）": "487eade0fb874e6e8962cc8f75b3f7bb",
        "MPC426 管弦乐学部琴房": "b7a5fcb27c054d55a712f2993cd04d07",
        "MPC427 管弦乐学部琴房": "6ba6de4ea11246d185485b52637d362b",
        "MPC428 管弦乐学部琴房": "56bfa46d5390495e826f017da64edc6c",
        "MPC429 管弦乐学部琴房": "de003fd87e844066b952800365abac8d",
        "MPC430 管弦乐学部琴房": "4b7c0c08d5ee45a09ba94dba907159cd",
        "MPC518 室内乐琴房（Double GP）": "9fa74f29bc8b494dacbecffa1a39ba0f",
        "MPC519 室内乐琴房（Double GP）": "eabe116377d5454981ae80af5dd13616",
        "MPC524室内乐琴房（Double GP）": "91bbe4ac68d04025bef15eb76abe5a3d",
    }

    if place not in FID_MAP:
        return "地点错误"

    url = "https://booking.cuhk.edu.cn/a/field/book/bizFieldBookMain/saveData"

    # ruleId 固定
    params = {"reBookMainId": "", "ruleId": RULE_ID}

    s = uuid.uuid4().hex
    data = {
        "id": s,
        "user.id": user_id,
        "userOrgId": "",
        "approvalFlag": "0",
        "bizFieldBookField.id": uuid.uuid4().hex,
        "bizFieldBookField.FId": FID_MAP[place],
        "bizFieldBookField.BId": s,
        "bizFieldBookField.theme": theme,
        "isNewRecord": "true",
        "extend1": EXTEND1,
        "userGrp": "Strings, Wind, Brass and Percussion（student）",
        "userTag": "Student",
        "bookType": "0",
        "fitBook": "false",
        "user.name": user_name,
        "userOrgName": "MUS",
        "userEmail": user_email,
        "userPhone": user_phone,
        "theme": theme,
        "bizFieldBookField.startTime": start_time,
        "bizFieldBookField.endTime": end_time,
        "bizFieldBookField.joinNums": "1",
        "extend18": "0",
        "bizFieldBookField.needRep": "0",
        "bizFieldBookField.extend1": "0",
        "extend16": "0",
        "bizFieldBookField.useDesc": "1",
    }

    try:
        c_request = CrazyRequests(proxies=proxies, cookie=cookie)
        response = c_request.post(url, params=params, data=data)
    except IOError as e:
        return "请求失败, 检查网络、代理服务器或 VPN"

    try:
        return response.json()["message"]
    except requests.exceptions.JSONDecodeError:
        return "Cookie 过期"


def timer_run(target_time: str, func):
    """
    target_time: 目标执行时间，格式 'YYYY-MM-DD HH:MM:SS'
    func: 要执行的函数引用
    """
    now = datetime.now()
    run_time = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
    delay = (run_time - now).total_seconds()
    if delay <= 0:
        func()
    else:
        timer = threading.Timer(delay, func)
        timer.start()
        return timer


if __name__ == "__main__":

    target_time = "2025-09-16 21:00:00"

    proxies: dict | None = {
        "http": "10.101.28.225:9000",
        "https": "10.101.28.225:9000",
    }
    # proxies: dict | None = None

    cookie: str = (
        "entry=normal; lang=zh_CN; jsession.id=e6e0dba0626f47de921d6c5049bd9d4b; JSESSIONID=5DF59B37DBAB3F9C2DAA6C14C4ADD53A; pathname=/a/field/client/main"
    )

    timer_run(
        target_time=target_time,
        func=lambda: print(
            book(
                cookie=cookie,
                user_id="124060073",
                user_name="徐思远",
                place="MPC327 管弦乐学部琴房（UP）",
                start_time="2025-09-17 20:00",
                end_time="2025-09-17 22:00",
                user_email="124060073@link.cuhk.edu.cn",
                user_phone="18354531357",
                theme="练琴",
                proxies=proxies,
            )
        ),
    )