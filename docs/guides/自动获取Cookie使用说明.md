# 自动获取Cookie功能使用说明

## 功能概述

v2版本新增了**自动获取Cookie**功能，无需再从浏览器开发者工具手动复制Cookie，大大简化了操作流程。

## 安装依赖

自动登录功能需要额外安装 `PySide6-WebEngine` 模块：

```bash
pip install PySide6-WebEngine
```

如果不安装此模块，程序仍可正常运行，但只能使用手动粘贴Cookie的方式。

## 使用方法

### 方式一：自动登录（推荐）

1. **启动程序**
   运行 `python GUI.py`

2. **点击Cookie按钮**
   点击主界面左上角的 "Cookie" 按钮（文件夹图标）

3. **选择自动登录**
   在弹出的对话框中，选择 **"自动登录"** 按钮

4. **登录预订系统**
   - 浏览器窗口会自动打开并访问 `https://booking.cuhk.edu.cn`
   - 在浏览器中输入您的学号和密码
   - 点击"登录"按钮

5. **自动捕获**
   - 登录成功后，程序会**自动检测并捕获Cookie**
   - 弹出提示"自动捕获成功"后，浏览器窗口自动关闭
   - Cookie已设置完成！

### 方式二：手动粘贴（传统方式）

如果自动登录失败或不可用，可以使用手动粘贴方式：

1. 点击主界面的 "Cookie" 按钮
2. 选择 **"手动粘贴"**
3. 按照传统方法从浏览器开发者工具复制Cookie
4. 粘贴到文本框中，点击保存

## 功能特性

### ✅ 智能登录检测

程序会自动检测以下URL特征，判断是否登录成功：
- `/field/client/main` （主页）
- `/field/book` （预订页面）

一旦检测到登录成功，自动开始捕获Cookie。

### ✅ Cookie完整性验证

捕获的Cookie必须包含以下关键字段才算有效：
- `JSESSIONID`
- `jsession.id`

如果Cookie不完整，会提示您重新登录。

### ✅ 代理服务器支持

如果您在"设置"中配置了代理服务器，自动登录窗口会自动应用代理设置。

支持的代理格式：
```
10.101.28.225:9000
```

### ✅ 错误处理

- **网络错误**：页面加载失败时会提示检查网络、代理或VPN
- **Cookie不完整**：自动验证Cookie有效性
- **模块缺失**：如果未安装QtWebEngine，会提示安装命令

### ✅ 手动捕获选项

如果自动捕获失败，您可以：
1. 在浏览器窗口中确认已完全登录
2. 点击窗口底部的 **"手动捕获Cookie并关闭"** 按钮

## 常见问题

### Q1: 自动登录窗口显示空白页？

**可能原因**：
- 网络连接问题
- 代理服务器配置错误
- 未在校园网内

**解决方案**：
1. 检查网络连接
2. 验证代理设置是否正确
3. 尝试点击"刷新"按钮
4. 如果仍然失败，使用"手动粘贴"方式

### Q2: 登录后没有自动捕获？

**可能原因**：
- 页面尚未完全加载
- Cookie未完全生成

**解决方案**：
1. 等待页面完全加载（进度条到100%）
2. 确认已跳转到预订系统主页
3. 点击 **"手动捕获Cookie并关闭"** 按钮

### Q3: 提示"Cookie不完整"？

**原因**：捕获的Cookie缺少必需的 `JSESSIONID` 或 `jsession.id` 字段

**解决方案**：
1. 确保已成功登录（而非停留在登录页）
2. 刷新页面并重新登录
3. 如果持续失败，使用手动粘贴方式

### Q4: 如何知道Cookie是否有效？

主界面会显示：
```
Cookie 已设置，最近更新时间：2025-10-24 14:30:00
```

如果显示此信息，说明Cookie已成功保存。

### Q5: QtWebEngine模块安装失败？

如果执行 `pip install PySide6-WebEngine` 失败：

1. **检查pip版本**：
   ```bash
   pip --version
   python -m pip install --upgrade pip
   ```

2. **使用国内镜像**：
   ```bash
   pip install PySide6-WebEngine -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. **检查Python版本**：
   确保Python版本 ≥ 3.10

## 技术细节

### 工作原理

1. **WebEngine浏览器**
   使用Qt WebEngine（基于Chromium内核）嵌入式浏览器

2. **Cookie监听**
   通过 `QWebEngineCookieStore` 监听所有新增的Cookie

3. **域名过滤**
   仅捕获域名包含 `cuhk.edu.cn` 的Cookie

4. **URL检测**
   监听URL变化，检测特征URL判断登录状态

5. **信号机制**
   使用Qt信号槽机制，Cookie捕获后发送信号给主窗口

### 新增文件

```
v2/Original/
├── GUI.py              # 已修改：添加AutoLoginDialog类和集成逻辑
├── test_webengine.py   # 新增：测试QtWebEngine可用性
└── test_auto_login.py  # 新增：测试自动登录功能
```

### 核心类

**AutoLoginDialog** (`GUI.py:760-956`)
- 继承自 `QtWidgets.QDialog`
- 包含 `QWebEngineView` 浏览器视图
- 信号：`cookie_captured(str)` - 捕获Cookie时发送

**关键方法**：
- `_on_url_changed()` - 智能登录检测
- `_auto_capture()` - 自动捕获Cookie
- `_validate_cookie()` - Cookie完整性验证
- `_apply_proxy()` - 应用代理设置

### 兼容性处理

如果 `QtWebEngine` 模块不可用，程序会：
1. 设置 `WEBENGINE_AVAILABLE = False`
2. 只提供手动粘贴方式
3. 不会崩溃或报错

## 开发信息

**功能状态**：✅ 已完成
**开发日期**：2025-10-24
**测试状态**：✅ 语法检查通过
**依赖版本**：
- PySide6 >= 6.5
- PySide6-WebEngine >= 6.5
- Python >= 3.10

## 后续优化计划

- [ ] 记住登录状态（保存session）
- [ ] 多账号Cookie管理
- [ ] Cookie有效期检测
- [ ] 无头模式（后台捕获）
- [ ] 验证码自动识别（如有）

---

**提示**：如果遇到问题，请先查看常见问题部分，或使用手动粘贴方式作为备选方案。
