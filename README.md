# MUS Booking System - 琴房预订系统

**版本**: 2.10.0
**最后更新**: 2025/10/25
**状态**: 生产就绪 ✅

一个为香港中文大学（深圳）音乐学院琴房预订系统设计的自动化预订工具，支持自动登录、智能代理检测、定时预订和批量预订功能。

---

## 目录

- [👥 面向用户](#-面向用户无开发经验)
  - [快速开始](#快速开始)
  - [功能介绍](#功能介绍)
  - [使用教程](#使用教程)
  - [常见问题](#常见问题)
  - [注意事项](#注意事项)
- [💻 面向开发者](#-面向开发者)
  - [项目架构](#项目架构)
  - [技术栈](#技术栈)
  - [开发环境搭建](#开发环境搭建)
  - [核心模块说明](#核心模块说明)
  - [构建与打包](#构建与打包)
  - [开发规范](#开发规范)
  - [贡献指南](#贡献指南)

---

# 👥 面向用户

本部分面向**没有编程经验的普通用户**，旨在帮助您快速上手使用本软件进行琴房预订。

## 快速开始

### 第一步：获取软件

1. **下载软件包**
   - 从提供方获取 `release.zip` 压缩包（约 207MB）
   - 或从项目 `release/` 文件夹获取

2. **解压文件**
   - 将压缩包解压到任意位置
   - 建议放在容易找到的位置（如 `C:\Program Files\MUS_Booking\` 或桌面）

3. **文件结构**
   ```
   MUS_Booking/
   ├── MUS_Booking.exe       ← 主程序（双击启动）
   ├── _internal/            ← 运行时依赖（不要删除！）
   ├── resources/            ← 资源文件
   │   └── CCA.ico
   └── config.yaml           ← 配置文件（自动生成）
   ```

### 第二步：准备网络环境

选择以下**任一方式**连接到学校网络：

#### 方式 1：校园网内（最简单）
```
✅ 连接校园 Wi-Fi
✅ 打开程序即可使用
```

#### 方式 2：AnyConnect VPN（推荐）
```
✅ 打开 Cisco AnyConnect
✅ 连接到学校 VPN
✅ 打开程序（自动检测 VPN）
```

#### 方式 3：Reqable 代理（备选）
```
✅ 打开 Reqable（端口设置为 9000）
✅ 打开程序（自动检测代理）
```

### 第三步：首次配置

1. **启动程序**
   - 双击 `MUS_Booking.exe`
   - 窗口标题为"魔丸"

2. **设置个人信息**
   - 点击左上角的"设置"按钮（📁 图标）
   - 填写以下信息：
     - **学号**（user_id）：如 `124060001`
     - **密码**（user_password）：学校账号密码，用于自动登录
     - **姓名**（user_name）：如 `张三`
     - **邮箱**（user_email）：如 `124060001@link.cuhk.edu.cn`
     - **电话**（user_phone）：如 `13800138000`
     - **主题**（theme）：默认 `练琴`
     - **代理**（proxies）：留空即可（程序会自动检测）
   - 点击"保存"

3. **验证网络配置**
   - 在设置对话框中，点击"自动检测"按钮
   - 查看检测结果：
     - ✅ "检测到可以直接连接（VPN 或校园网）" → 完美！
     - ✅ "检测到可用代理：127.0.0.1:9000" → 使用 Reqable
     - ❌ 如果失败，请检查网络连接

### 第四步：开始预订

1. **添加预订请求**
   - 点击"+ 添加一组预定请求"
   - 选择：
     - **琴房**：如 `MPC327 管弦乐学部琴房（UP）`
     - **日期**：预订日期（如明天）
     - **开始时间**：如 `19:00`
     - **结束时间**：如 `21:00`
   - 可以添加多个琴房作为备选

2. **设置启动时间**
   - **立即启动**：勾选"立即启动"复选框
   - **定时启动**：设置具体时间（如 `2025-10-26 21:00:00`）

3. **执行预订**
   - 点击大大的"开始"按钮
   - 程序会自动：
     1. 打开浏览器窗口（自动登录）
     2. 填写学号和密码
     3. 捕获 Cookie
     4. 关闭浏览器
     5. 开始预订
   - **无需手动操作**，等待即可

4. **查看结果**
   - 在底部"运行日志"窗口查看实时进度
   - 成功示例：`[预订成功] MPC327 19:00-21:00`
   - 失败示例：`[预订失败] 手速太慢，琴房已被预订`

---

## 功能介绍

### 1. 自动登录获取 Cookie
- 点击"开始"后，程序会自动打开浏览器窗口
- 自动填写学号和密码
- 自动提交登录表单
- 捕获有效的 Cookie
- 关闭浏览器窗口
- **全程无需手动操作**

### 2. 智能代理检测
- 程序启动时自动检测网络环境
- 优先级：
  1. 测试直接连接（校园网或 VPN）
  2. 检测 Reqable 代理（127.0.0.1:9000）
  3. 检测系统代理
- 手动检测：点击"Cookie"按钮 → "自动检测代理"

### 3. 定时预订
- **立即启动**：勾选后，点"开始"立即执行预订
- **定时启动**：设置启动时间，程序会在指定时间自动开始
- 适合在琴房开放预订的瞬间抢房

### 4. 批量预订
- 可以添加多个琴房作为备选方案
- 程序会按顺序尝试每个琴房
- 一旦成功预订，停止后续请求
- 超过 2 小时的时段会自动拆分为多个 2 小时时段

### 5. 自动时段拆分
- 琴房预订系统限制每次预订最多 2 小时
- 如果您设置了 `19:00-23:00`（4 小时）
- 程序会自动拆分为：
  - `19:00-21:00`
  - `21:00-23:00`
- 依次提交预订

---

## 使用教程

### 场景 1：抢热门琴房

**目标**：在 21:00 琴房开放预订时，立即抢到 MPC327

**步骤**：
1. 提前 10 分钟打开程序
2. 连接 AnyConnect VPN
3. 添加预订请求：`MPC327`，明天 `19:00-21:00`
4. 设置启动时间为 `今天 21:00:00`
5. 点击"开始"
6. 等待自动执行

**技巧**：
- 可以添加多个琴房作为备选（如 MPC327、MPC328、MPC329）
- 设置启动时间提前 1-2 秒（如 `20:59:58`）

### 场景 2：批量预订一周琴房

**目标**：一次性预订本周 7 天的琴房

**步骤**：
1. 点击"+ 添加一组预定请求"多次，添加 7 个请求
2. 每个请求设置不同的日期：
   - 请求 1：`2025-10-26 19:00-21:00`
   - 请求 2：`2025-10-27 19:00-21:00`
   - ...
   - 请求 7：`2025-11-01 19:00-21:00`
3. 勾选"立即启动"
4. 点击"开始"

**注意**：
- 确保 Cookie 有效（如过期，程序会提示重新获取）

### 场景 3：更新 Cookie

**场景**：Cookie 过期，需要重新获取

**步骤**：
1. 点击"Cookie"按钮
2. 选择"自动登录"
3. 等待浏览器窗口自动登录
4. Cookie 自动捕获并保存
5. 关闭对话框

**或者手动粘贴**：
1. 打开浏览器，登录 `booking.cuhk.edu.cn`
2. 按 F12 打开开发者工具
3. 进入"Network"（网络）标签
4. 刷新页面
5. 找到请求，复制 Cookie
6. 点击"Cookie"按钮 → 粘贴到文本框 → 保存

---

## 常见问题

### Q1: 程序无法启动，提示缺少 DLL 文件

**原因**：缺少 Visual C++ 运行库

**解决方法**：
1. 下载并安装：https://aka.ms/vs/17/release/vc_redist.x64.exe
2. 重启电脑后再试

---

### Q2: Cookie 获取失败

**可能原因**：
- ❌ Reqable 未启动或端口不是 9000
- ❌ AnyConnect VPN 未连接
- ❌ 学号或密码错误
- ❌ 网络连接问题

**解决方法**：
1. 检查 Reqable 是否运行（如果使用 Reqable）
2. 检查 AnyConnect VPN 连接状态（如果使用 VPN）
3. 在"设置"中确认学号、密码正确
4. 查看日志窗口的详细错误信息
5. 尝试手动粘贴 Cookie（见上方教程）

---

### Q3: 预订失败，提示"Cookie 过期"

**原因**：Cookie 有效期已过（通常几小时到几天）

**解决方法**：
- 重新点击"开始"，程序会自动获取新 Cookie
- 或手动点击"Cookie" → "自动登录"

---

### Q4: 预订失败，提示"请求失败，检查网络、代理服务器或 VPN"

**可能原因**：
- ❌ 网络连接问题
- ❌ 代理设置错误
- ❌ VPN 断开

**解决方法**：
1. 检查网络连接
2. 重新启动 Reqable（如果使用）
3. 重新连接 AnyConnect VPN（如果使用）
4. 点击"Cookie"按钮 → "自动检测代理"
5. 如果仍然失败，尝试切换连接方式（VPN ↔ Reqable）

---

### Q5: 预订失败，提示"手速太慢"

**原因**：琴房已被其他用户预订

**解决方法**：
- 选择其他琴房或时段
- 在开放预订的瞬间启动程序（设置定时）
- 提前 1-2 秒启动（如开放时间是 21:00:00，设置为 20:59:58）

---

### Q6: 杀毒软件报毒

**原因**：这是误报，打包的 .exe 程序经常被误报为病毒

**解决方法**：
- 添加到杀毒软件的信任列表/白名单
- 或临时关闭杀毒软件
- **本软件是开源的**，所有代码可在 `src/` 目录查看

---

### Q7: 如何切换连接方式？

**从 Reqable 切换到 VPN**：
1. 关闭 Reqable
2. 打开 AnyConnect 并连接
3. 打开程序"设置"
4. 清空 proxies 文本框
5. 点击"自动检测"
6. 保存

**从 VPN 切换到 Reqable**：
1. 打开 Reqable
2. 打开程序"设置"
3. 点击"自动检测"
4. 会自动检测到 Reqable（127.0.0.1:9000）
5. 保存

---

## 注意事项

### 安全与隐私

- ✅ 学号、密码等信息**仅保存在本地** `config.yaml` 文件中
- ✅ **不会上传到任何服务器**
- ✅ 仅用于自动登录学校系统
- ✅ Cookie 信息也仅本地存储

### 文件管理

- ❌ **不要删除或移动** `_internal/` 文件夹
- ❌ **不要单独移动** `MUS_Booking.exe`
- ✅ 可以创建桌面快捷方式
- ✅ `config.yaml` 文件会自动生成，可以手动编辑（YAML 格式）

### 使用技巧

1. **提前准备**
   - 在开放预订前 5-10 分钟准备好
   - 确保网络连接稳定
   - 提前测试自动登录是否正常

2. **批量备选**
   - 添加多个琴房作为备选方案
   - 提高预订成功率

3. **定期更新 Cookie**
   - Cookie 会过期，建议每次预订前重新获取
   - 或在程序提示 Cookie 过期时重新获取

4. **查看日志**
   - 底部"运行日志"窗口会显示详细的执行过程
   - 如遇问题，截图日志并联系技术支持

---

## 更新日志

### v2.10.0

- ✅ 独立可执行文件版本
- ✅ 包含所有依赖，无需安装 Python
- ✅ 自动登录获取 Cookie
- ✅ 智能代理检测
- ✅ 定时预订功能
- ✅ 多琴房批量预订

### v2.8

- ✅ 原生支持 AnyConnect VPN
- ✅ 不再需要 Reqable 中转
- ✅ 自动检测校园网
- ✅ 智能连接方式切换

### v2.6
- ✅ 完全无人值守自动登录

### v2.4
- ✅ 渐进式表单自动化

---

## 技术支持

如果遇到无法解决的问题：

1. 查看程序底部的"运行日志"窗口
2. 截图错误信息
3. 联系开发者或查看项目文档

---

# 💻 面向开发者

本部分面向**有编程经验的开发者**，介绍项目架构、技术栈和进一步开发指南。

## 项目架构

### 整体架构

本项目采用 **MVC（Model-View-Controller）** 架构模式，使用 **PySide6（Qt6）** 作为 GUI 框架。

```
┌─────────────────────────────────────────────────────────┐
│                     MUS Booking System                  │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    View     │  │  Controller  │  │    Model     │  │
│  │  (PySide6)  │◄─┤  (MainWindow)│─►│   (Config)   │  │
│  │             │  │              │  │              │  │
│  │  - Dialogs  │  │  - Workers   │  │  - Data      │  │
│  │  - Widgets  │  │  - Signals   │  │  - YAML      │  │
│  └─────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  │         │
│         └──────────────────┼──────────────────┘         │
│                            │                            │
│                  ┌─────────▼──────────┐                │
│                  │   Core Logic       │                │
│                  │  (main.py)         │                │
│                  │                    │                │
│                  │  - book()          │                │
│                  │  - timer_run()     │                │
│                  │  - CrazyRequests   │                │
│                  └────────────────────┘                │
│                            │                            │
│                  ┌─────────▼──────────┐                │
│                  │   Network Layer    │                │
│                  │  (requests)        │                │
│                  │                    │                │
│                  │  - HTTP/HTTPS      │                │
│                  │  - Proxy Support   │                │
│                  │  - SSL Handling    │                │
│                  └────────────────────┘                │
└─────────────────────────────────────────────────────────┘
```

### 目录结构

```
mus-booking/
│
├── 📂 src/                          # 源代码目录
│   ├── __init__.py
│   ├── main.py                      # 核心预订逻辑
│   ├── main_window.py               # 主窗口（从 GUI.py 提取）
│   ├── config.py                    # 配置管理
│   ├── constants.py                 # 常量定义
│   ├── utils.py                     # 工具函数
│   ├── workers.py                   # 后台线程
│   ├── proxy_detector.py            # 智能代理检测
│   ├── GUI.py                       # 旧版单体文件（2100+ 行，保留兼容）
│   │
│   ├── 📂 widgets/                  # 自定义 UI 组件
│   │   ├── __init__.py
│   │   ├── wheel_combo.py           # 滚轮组合框
│   │   ├── date_wheel.py            # 日期选择器
│   │   ├── time_wheel.py            # 时间选择器
│   │   └── request_item.py          # 预订请求编辑项
│   │
│   └── 📂 dialogs/                  # 对话框窗口
│       ├── __init__.py
│       ├── settings_dialog.py       # 设置对话框
│       ├── cookie_dialog.py         # Cookie/代理设置对话框
│       └── auto_login_dialog.py     # 自动登录对话框
│
├── 📂 resources/                    # 资源文件
│   └── CCA.ico                      # 应用图标
│
├── 📂 docs/                         # 文档
│   ├── 📂 changelog/                # 版本更新说明
│   ├── 📂 guides/                   # 用户指南
│   ├── PROJECT_STRUCTURE.md         # 项目结构文档
│   └── ...
│
├── 📂 tests/                        # 测试套件
│   ├── test_connection.py           # 网络连接测试
│   ├── test_ssl_detail.py           # SSL 测试
│   ├── test_qt_proxy.py             # Qt 代理测试
│   └── ...
│
├── 📂 release/                      # 发布版本
│   ├── MUS_Booking.exe              # 可执行文件
│   └── _internal/                   # 运行时依赖
│
├── 📄 config.yaml                   # 配置文件
├── 📄 requirements.txt              # Python 依赖
├── 📄 run.py                        # 入口点
├── 📄 build.bat                     # 构建脚本（Windows）
├── 📄 build.spec                    # PyInstaller 配置
└── 📄 README.md                     # 本文件
```

---

## 技术栈

### 前端框架
- **PySide6 (Qt 6.4+)** - 跨平台 GUI 框架
  - `QtCore` - 核心非 GUI 功能
  - `QtGui` - GUI 相关类
  - `QtWidgets` - UI 组件
  - `QtNetwork` - 网络功能
  - `QtWebEngineWidgets` - 内嵌浏览器（用于自动登录）
  - `QtWebEngineCore` - Web 引擎核心

### 后端与网络
- **requests (>=2.28.0)** - HTTP 客户端库
- **urllib3 (>=1.26.0)** - 底层 HTTP 库
- **自定义 CrazyRequests 类** - 智能 SSL 错误处理包装器

### 配置与数据
- **PyYAML (>=6.0)** - YAML 文件解析
- **dataclasses** - 类型安全的配置结构
- **json** - JSON 解析（内部使用）

### 构建与打包
- **PyInstaller (>=5.0.0)** - Python 转可执行文件
- **build.spec** - PyInstaller 配置（多文件模式）

### 平台特定
- **winreg** - Windows 注册表访问（检测 AnyConnect VPN）
- **subprocess** - 进程管理（代理检测）

### 开发与测试
- **Python 3.11+** - 编程语言
- **自定义测试套件** - 6 个测试模块

---

## 开发环境搭建

### 1. 克隆项目

```bash
git clone <repository_url>
```

### 2. 安装 Python

- 下载并安装 **Python 3.11+**
- 下载链接：https://www.python.org/downloads/
- 安装时勾选"Add Python to PATH"

### 3. 创建虚拟环境（推荐）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

依赖列表：
```
PySide6>=6.4.0           # Qt6 GUI框架
PySide6-WebEngine>=6.4.0 # Web引擎（用于自动登录）
PyYAML>=6.0              # YAML配置文件解析
requests>=2.28.0         # HTTP请求库
urllib3>=1.26.0          # HTTP客户端库
pyinstaller>=5.0.0       # 打包为可执行文件（可选）
```

### 5. 运行程序

#### 方式 1：使用入口点（推荐）

```bash
python run.py
```

#### 方式 2：直接运行 GUI（兼容旧方式）

```bash
cd src
python GUI.py
```

#### 方式 3：作为模块运行

```bash
python -m src.GUI
```

### 6. 运行测试

```bash
# 网络连接测试
python tests/test_connection.py

# SSL 详细信息测试
python tests/test_ssl_detail.py

# Qt 代理配置测试
python tests/test_qt_proxy.py

# 预订请求测试
python tests/test_booking_request.py

# 自动登录测试
python tests/test_auto_login.py

# WebEngine 测试
python tests/test_webengine.py
```

---

## 核心模块说明

### 1. `main.py` - 核心预订逻辑

**主要类和函数**：

#### `CrazyRequests` 类

智能 HTTP 请求包装器，处理 SSL 错误和代理配置。

```python
class CrazyRequests:
    def __init__(self, proxies: dict | None = None, cookie: str = ""):
        """
        初始化请求会话

        参数:
            proxies: 代理配置字典，None 或 {} 表示直接连接
            cookie: Cookie 字符串
        """
        self.proxies = proxies
        self.use_proxy = proxies is not None and len(proxies) > 0
        self.session = requests.Session()

        # 如果不使用代理，禁用环境变量检测
        if not self.use_proxy:
            self.session.trust_env = False

    def get(self, url, params=None):
        """GET 请求，自动处理 SSL 错误"""
        # 直接连接时先尝试 verify=True，失败则 verify=False
        # 使用代理时直接 verify=False

    def post(self, url, params=None, data=None, json=None):
        """POST 请求，自动处理 SSL 错误"""
```

**SSL 验证策略**：
1. **直接连接**：
   - 优先尝试 `verify=True`（启用 SSL 验证）
   - 如果 SSL 错误，自动重试 `verify=False`（兼容特殊 VPN 配置）
2. **使用代理**：
   - 直接使用 `verify=False`（兼容 HTTPS 代理）

#### `book()` 函数

```python
def book(
    place: str,
    user_id: str,
    user_name: str,
    user_email: str,
    user_phone: str,
    date_str: str,      # YYYY-MM-DD
    start: str,         # HH:MM
    end: str,           # HH:MM
    theme: str,
    proxies: dict | None = None,
    cookie: str = ""
) -> str:
    """
    执行单次预订请求

    返回:
        成功消息或错误消息
    """
```

**工作流程**：
1. 构建预订请求数据
2. 发送 POST 请求到 `booking.cuhk.edu.cn/book`
3. 解析响应 JSON
4. 返回成功/失败消息

#### `timer_run()` 函数

```python
def timer_run(target_time: datetime, func, *args, **kwargs):
    """
    定时器启动函数

    参数:
        target_time: 目标执行时间
        func: 要执行的函数
        *args, **kwargs: 函数参数
    """
```

**工作流程**：
1. 计算延迟时间（target_time - 当前时间）
2. 如果延迟 > 0，等待
3. 执行函数

---

### 2. `main_window.py` - 主窗口

**主要类**：

#### `MainWindow` 类

```python
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        """初始化主窗口"""
        # 加载配置
        self.cfg = ConfigManager.load()

        # 自动检测代理
        self._auto_detect_proxy_on_startup()

        # 构建 UI
        self._build_ui()
```

**主要方法**：
- `_build_ui()` - 构建用户界面
- `_auto_detect_proxy_on_startup()` - 启动时自动检测代理
- `on_start_clicked()` - "开始"按钮点击事件
- `on_stop_clicked()` - "停止"按钮点击事件
- `_add_request_item()` - 添加预订请求项
- `_save_config()` - 保存配置到 YAML

---

### 3. `config.py` - 配置管理

**主要类**：

#### `RequestItemData` 数据类

```python
@dataclass
class RequestItemData:
    place: str = PLACES[0]
    date: str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    start: str = "19:00"
    end: str = "21:00"
```

#### `AppConfig` 数据类

```python
@dataclass
class AppConfig:
    target_time: str = datetime.now().strftime("%Y-%m-%d 21:00:00")
    start_immediately: bool = False

    proxies: str = ""
    cookie: str = ""
    cookie_updated_at: str = ""

    user_id: str = ""
    user_password: str = ""
    user_name: str = ""
    user_email: str = ""
    user_phone: str = ""
    theme: str = "练琴"

    requests: List[RequestItemData] = None
```

#### `ConfigManager` 类

```python
class ConfigManager:
    @staticmethod
    def load(path: str = CONFIG_FILE) -> AppConfig:
        """从 YAML 文件加载配置"""

    @staticmethod
    def save(cfg: AppConfig, path: str = CONFIG_FILE):
        """保存配置到 YAML 文件"""
```

---

### 4. `proxy_detector.py` - 智能代理检测

**主要类**：

#### `ProxyDetector` 类

```python
class ProxyDetector:
    @staticmethod
    def auto_detect() -> tuple[bool, str, dict | None]:
        """
        自动检测可用的网络配置

        返回:
            (成功标志, 描述信息, 代理字典)
        """

    @staticmethod
    def test_proxy(proxy_dict: dict | None) -> tuple[bool, str]:
        """
        测试代理是否可用

        返回:
            (成功标志, 描述信息)
        """

    @staticmethod
    def is_anyconnect_connected() -> bool:
        """检测 AnyConnect VPN 是否已连接"""
```

**检测优先级**：
1. 测试直接连接（校园网或 VPN）
2. 检测 Reqable（127.0.0.1:9000）
3. 检测系统代理
4. 都不可用 → 提示用户配置

---

### 5. `workers.py` - 后台线程

**主要类**：

#### `BookingWorker` 类

```python
class BookingWorker(QtCore.QThread):
    log_signal = QtCore.Signal(str)
    finished_signal = QtCore.Signal()

    def __init__(self, ...):
        """初始化预订工作线程"""

    def run(self):
        """执行预订任务（在后台线程）"""
```

**工作流程**：
1. 如果 `start_immediately=False`，等待到 `target_time`
2. 对每个预订请求：
   - 拆分时段（如果 > 2 小时）
   - 调用 `book()` 函数
   - 发送日志信号到主线程
3. 发送完成信号

---

### 6. `widgets/` - 自定义 UI 组件

#### `wheel_combo.py` - `WheelCombo`

滚轮组合框，支持鼠标滚轮切换选项。

```python
class WheelCombo(QtWidgets.QComboBox):
    def wheelEvent(self, event):
        """重写滚轮事件"""
```

#### `date_wheel.py` - `DateWheel`

日期选择器，包含年、月、日三个滚轮组合框。

```python
class DateWheel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        """初始化日期选择器"""
        # 年份、月份、日期组合框
```

#### `time_wheel.py` - `TimeWheel`

时间选择器，包含小时、分钟两个滚轮组合框。

```python
class TimeWheel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        """初始化时间选择器"""
        # 小时、分钟组合框

class MinuteToggle(QtWidgets.QWidget):
    """分钟切换按钮（00、15、30、45）"""
```

#### `request_item.py` - `RequestItemWidget`

预订请求编辑项，包含琴房、日期、时间选择器。

```python
class RequestItemWidget(QtWidgets.QWidget):
    def __init__(self, data: RequestItemData, parent=None):
        """初始化预订请求编辑项"""
        # 琴房下拉框、日期选择器、时间选择器

    def get_data(self) -> RequestItemData:
        """获取当前数据"""
```

---

### 7. `dialogs/` - 对话框窗口

#### `settings_dialog.py` - `SettingsDialog`

设置对话框，编辑用户信息和代理配置。

```python
class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, cfg: AppConfig, parent=None):
        """初始化设置对话框"""
        # 学号、密码、姓名、邮箱、电话、主题、代理

    def auto_detect_proxy(self):
        """自动检测代理"""
```

#### `cookie_dialog.py` - `CookieDialog`

Cookie 和代理设置对话框。

```python
class CookieDialog(QtWidgets.QDialog):
    def __init__(self, cfg: AppConfig, parent=None):
        """初始化 Cookie 对话框"""
        # Cookie 文本框、代理设置、自动检测
```

#### `auto_login_dialog.py` - `AutoLoginDialog`

自动登录对话框，使用 QWebEngineView 自动登录并捕获 Cookie。

```python
class AutoLoginDialog(QtWidgets.QDialog):
    cookie_captured = QtCore.Signal(str)

    def __init__(self, user_id: str, user_password: str, ...):
        """初始化自动登录对话框"""
        # QWebEngineView、自动填表、Cookie 捕获

    def on_load_finished(self, ok):
        """页面加载完成事件"""
        # 自动填写学号、密码、提交

    def capture_cookie(self):
        """捕获 Cookie"""
```

---

## 构建与打包

### 使用 PyInstaller 打包

本项目使用 **PyInstaller** 将 Python 程序打包为独立的 Windows 可执行文件（.exe）。

#### 1. 自动构建（推荐）

使用提供的构建脚本：

```bash
# Windows
build.bat
```

`build.bat` 内容：

```batch
@echo off
echo ========================================
echo MUS Booking System - Build Script
echo ========================================

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [OK] Python is installed

REM 检查 PyInstaller 是否安装
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] PyInstaller is not installed, installing...
    pip install pyinstaller
)

echo [OK] PyInstaller is ready

REM 安装依赖
echo [INFO] Installing dependencies...
pip install -r requirements.txt

REM 构建可执行文件
echo [INFO] Building executable...
pyinstaller build.spec

echo ========================================
echo Build completed!
echo Output: dist\MUS_Booking\
echo ========================================
pause
```

#### 2. 手动构建

```bash
# 安装依赖
pip install -r requirements.txt

# 使用 build.spec 构建
pyinstaller build.spec
```

#### 3. `build.spec` 配置

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),  # 包含资源文件
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MUS_Booking',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources\\CCA.ico',  # 应用图标
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MUS_Booking',
)
```

**关键配置**：

- `console=False` - 不显示控制台窗口（GUI 应用）
- `icon='resources\\CCA.ico'` - 应用图标
- `datas=[('resources', 'resources')]` - 包含资源文件

#### 4. 输出结构

```
dist/MUS_Booking/
├── MUS_Booking.exe              # 主可执行文件
├── _internal/                   # PyInstaller 运行时依赖
│   ├── python311.dll
│   ├── PySide6/                 # Qt 库
│   │   ├── Qt6Core.dll
│   │   ├── Qt6Gui.dll
│   │   ├── Qt6Widgets.dll
│   │   ├── Qt6WebEngineCore.dll
│   │   └── ...
│   ├── certifi/
│   ├── requests/
│   └── ...
└── resources/
    └── CCA.ico
```

**文件大小**：约 207MB（包含所有依赖）

---

## 开发规范

### 代码风格

1. **遵循 PEP 8**
   - 使用 4 空格缩进
   - 每行最多 120 字符
   - 函数和类之间空 2 行

2. **编码声明**
   ```python
   # -*- coding: utf-8 -*-
   ```

3. **类型注解**
   ```python
   def book(place: str, user_id: str, ...) -> str:
       pass
   ```

4. **文档字符串**
   ```python
   def auto_detect() -> tuple[bool, str, dict | None]:
       """
       自动检测可用的网络配置
   
       返回:
           (成功标志, 描述信息, 代理字典)
       """
   ```

### 注释规范

1. **模块注释**
   ```python
   # -*- coding: utf-8 -*-
   """
   MainWindow主窗口
   从 GUI.py 提取的模块
   """
   ```

2. **函数注释**
   - 关键函数包含详细的文档字符串
   - 复杂逻辑添加行内注释

3. **使用中文注释**（便于理解业务逻辑）
   ```python
   # 如果不使用代理，禁用环境变量检测
   if not self.use_proxy:
       self.session.trust_env = False
   ```

### 调试日志

使用统一的日志前缀标识模块：

```python
print("[模块名] 日志信息")
```

**示例**：
```python
print("[AutoLogin] Cookie已捕获: entry")
print("[ProxyDetector] [OK] 找到可用代理: Reqable")
print("[启动] [ERROR] 自动检测网络配置失败: {e}")
```

**日志级别**：
- `[OK]` - 成功
- `[INFO]` - 信息
- `[WARNING]` - 警告
- `[ERROR]` - 错误

### Git 提交规范

使用 **Conventional Commits** 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型（type）**：
- `feat` - 新功能
- `fix` - 修复 bug
- `docs` - 文档
- `style` - 代码格式
- `refactor` - 重构
- `test` - 测试
- `chore` - 构建/工具

**示例**：
```
feat(proxy): add intelligent proxy detection

- Auto-detect Reqable proxy (127.0.0.1:9000)
- Auto-detect AnyConnect VPN connection
- Fallback to system proxy
- Test proxy availability before use

Closes #12
```

---

## 贡献指南

### 1. Fork 项目

点击项目页面右上角的"Fork"按钮。

### 2. 克隆到本地

```bash
git clone <your_fork_url>
cd "mus-booking"
```

### 3. 创建分支

```bash
git checkout -b feature/your-feature-name
```

### 4. 进行修改

按照开发规范进行代码修改。

### 5. 运行测试

```bash
# 确保所有测试通过
python tests/test_connection.py
python tests/test_booking_request.py
```

### 6. 提交更改

```bash
git add .
git commit -m "feat: add your feature description"
```

### 7. 推送到远程

```bash
git push origin feature/your-feature-name
```

### 8. 创建 Pull Request

在 GitHub 上创建 Pull Request。

---

## 进阶开发

### 1. 添加新的琴房

编辑 `src/constants.py`：

```python
PLACES = [
    "MPC327 管弦乐学部琴房（UP）",
    "MPC328 管弦乐学部琴房（UP）",
    # 添加新琴房
    "MPC329 管弦乐学部琴房（UP）",
]
```

### 2. 修改 UI 样式

编辑 `src/main_window.py` 中的样式表：

```python
app.setStyleSheet("""
    QMainWindow {
        background-color: #f0f0f0;
    }
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
""")
```

### 3. 添加新的自动化功能

在 `src/main.py` 中添加新函数：

```python
def batch_book(requests: List[RequestItemData], ...):
    """批量预订函数"""
    results = []
    for req in requests:
        result = book(
            place=req.place,
            date_str=req.date,
            start=req.start,
            end=req.end,
            ...
        )
        results.append(result)
    return results
```

### 4. 扩展代理检测

在 `src/proxy_detector.py` 中添加新的检测方法：

```python
@staticmethod
def detect_custom_proxy() -> tuple[bool, dict | None]:
    """检测自定义代理"""
    # 实现检测逻辑
    return (True, {"http": "...", "https": "..."})
```

### 5. 添加数据库支持

安装数据库库：

```bash
pip install sqlalchemy
```

创建 `src/database.py`：

```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class BookingHistory(Base):
    __tablename__ = 'booking_history'

    id = Column(Integer, primary_key=True)
    place = Column(String)
    date = Column(String)
    start = Column(String)
    end = Column(String)
    result = Column(String)

engine = create_engine('sqlite:///booking.db')
Base.metadata.create_all(engine)
```

---

## 常见开发问题

### Q1: 如何调试 PyInstaller 打包后的程序？

**方法 1：启用控制台**

修改 `build.spec`：

```python
exe = EXE(
    ...
    console=True,  # 修改为 True
    ...
)
```

**方法 2：查看日志文件**

在代码中添加日志输出到文件：

```python
import logging

logging.basicConfig(
    filename='debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.debug("Debug message")
```

### Q2: 如何处理 QWebEngineView 在打包后无法加载的问题？

确保 PyInstaller 包含了所有 WebEngine 依赖：

```python
# build.spec
hiddenimports=[
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineCore',
],
```

### Q3: 如何减小打包后的文件大小？

1. **排除不必要的模块**

```python
# build.spec
excludes=[
    'tkinter',
    'matplotlib',
    'numpy',
],
```

2. **使用 UPX 压缩**

```python
# build.spec
upx=True,
```

3. **使用单文件模式**（不推荐，启动慢）

```bash
pyinstaller --onefile run.py
```

---

## 项目维护

### 版本管理

- **主分支**: `main`
- **开发分支**: `develop`
- **功能分支**: `feature/*`
- **修复分支**: `fix/*`

### 发布流程

1. 在 `develop` 分支开发新功能
2. 测试通过后合并到 `main`
3. 打标签：`git tag v2.10.0`
4. 推送标签：`git push origin v2.10.0`
5. 构建发布版本：`build.bat`
6. 上传到发布平台

### 文档更新

每次发布新版本时更新：
- `README.md` - 更新版本号和更新日志
- `docs/changelog/v*.md` - 添加新版本更新说明
- `docs/guides/` - 更新用户指南（如有必要）

---

## 技术支持

### 开发者社区

- **GitHub Issues**: 报告 bug 或提出功能请求
- **GitHub Discussions**: 技术讨论和问答

### 联系方式

- **开发者**: CCA
- **邮箱**: sichenwang@cuhk.edu.cn 

---

## 许可证

本项目采用 **MIT License**。

```
MIT License

Copyright (c) 2025 MUS Booking System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 致谢

- **PySide6** - 提供强大的 GUI 框架
- **requests** - 提供简洁的 HTTP 库
- **PyInstaller** - 提供便捷的打包工具
