# Bug 修复说明 - QWebEngineView 代理问题

## 问题描述

**现象：** 即使 AnyConnect VPN 已连接，浏览器可以正常访问学校网站，但程序的自动登录窗口（QWebEngineView）仍然显示"chrome-error://chromewebdata/"错误，提示"检查代理服务器地址"。

**根本原因：**
- `requests` 库的连接设置已正确（通过 `session.trust_env = False`）
- 但 **QWebEngineView 的代理设置未正确处理**
- 当 `proxies` 配置为空时，代码直接返回，没有明确禁用代理
- QWebEngineView 继承了系统代理设置或之前的代理配置

---

## 修复方案

### 修改文件：`GUI.py`

**修改位置：** `_apply_proxy` 方法（AutoLoginDialog 类）

**修改前：**
```python
def _apply_proxy(self, proxies_config: str):
    """应用代理设置"""
    if not proxies_config:
        return  # ❌ 问题：直接返回，没有禁用代理

    # ... 应用代理的代码
```

**修改后：**
```python
def _apply_proxy(self, proxies_config: str):
    """应用代理设置（或明确禁用代理）"""
    try:
        # 如果没有配置代理，明确禁用代理（直接连接）
        if not proxies_config or not proxies_config.strip():
            proxy = QtNetwork.QNetworkProxy()
            proxy.setType(QtNetwork.QNetworkProxy.NoProxy)  # ✅ 关键：明确设置为无代理
            QtNetwork.QNetworkProxy.setApplicationProxy(proxy)
            self.status_label.setText("使用直接连接（无代理）")
            print("[AutoLoginDialog] 已设置为直接连接（NoProxy）")
            return

        # ... 应用代理的代码（如果配置了代理）
    except Exception as e:
        # 出错时也禁用代理
        proxy = QtNetwork.QNetworkProxy()
        proxy.setType(QtNetwork.QNetworkProxy.NoProxy)
        QtNetwork.QNetworkProxy.setApplicationProxy(proxy)
        self.status_label.setText("代理设置失败，使用直接连接")
```

---

## 测试步骤

### 前提条件

1. ✅ AnyConnect VPN 已安装并连接
2. ✅ 浏览器可以正常访问 `https://booking.cuhk.edu.cn`
3. ✅ 已更新代码文件（GUI.py）

### 测试 1：验证 Qt 代理设置

```bash
cd "项目目录"
python test_qt_proxy.py
```

**预期结果：**
```
[OK] 已设置 NoProxy
当前代理类型: ProxyType.NoProxy
[OK] 验证成功：当前为直接连接模式

[OK] 已设置 HTTP 代理
当前代理类型: ProxyType.HttpProxy
[OK] 验证成功：代理设置已生效
```

### 测试 2：清空配置文件中的代理

编辑 `config.yaml`：

```yaml
proxies: ''  # 清空或设置为空字符串
```

或者完全删除这一行：

```yaml
# proxies 行已删除
```

### 测试 3：启动 GUI 程序

```bash
python GUI.py
```

**预期日志（控制台输出）：**
```
[启动] 配置文件中未设置代理，开始自动检测网络配置...
[ProxyDetector] 步骤0：测试直接连接（校园网内或VPN）...
[ProxyDetector] [OK] 可以直接连接到学校网站！
[ProxyDetector] 检测到 AnyConnect VPN 已连接
[ProxyDetector] 建议：不使用代理，直接通过VPN访问
[启动] 检测到可以直接连接到学校网站（校园网内或 AnyConnect VPN 已连接）
```

### 测试 4：自动登录功能

1. 点击"Cookie"按钮 → 选择"自动登录获取"
2. 观察自动登录窗口

**预期现象：**
- ✅ 状态栏显示："使用直接连接（无代理）"
- ✅ 页面正常加载（不再显示 chrome-error）
- ✅ 可以看到 CUHK 登录页面
- ✅ 自动填写学号和密码
- ✅ 成功捕获 Cookie

**预期控制台日志：**
```
[AutoLoginDialog] 已设置为直接连接（NoProxy）
```

---

## 验证要点

### ✅ 成功标志

1. **自动登录窗口加载正常**
   - URL 显示为 `https://booking.cuhk.edu.cn/...`
   - 不再是 `chrome-error://chromewebdata/`

2. **状态栏显示正确**
   - "使用直接连接（无代理）"
   - 不是"已应用代理: ..."

3. **控制台日志正确**
   - `[AutoLoginDialog] 已设置为直接连接（NoProxy）`
   - 没有 `[AutoLogin] Current URL: chrome-error://chromewebdata/` 错误

4. **自动填写和登录成功**
   - 自动点击 Login 按钮
   - 自动填写学号和密码
   - 成功跳转到预订页面
   - 自动捕获 Cookie

---

## 可能遇到的问题

### 问题 1：仍然显示 chrome-error

**原因：** 可能是缓存问题或代理设置未清除

**解决：**
```bash
# 1. 完全退出程序
# 2. 清空配置文件中的 proxies
# 3. 重启程序
python GUI.py
```

### 问题 2：页面加载很慢

**原因：** DNS 解析或 VPN 连接不稳定

**解决：**
```bash
# 检查 VPN 连接状态
ipconfig /all | findstr "Cisco AnyConnect"

# 测试网络连接
ping booking.cuhk.edu.cn
```

### 问题 3：控制台没有显示日志

**原因：** 日志被重定向或控制台编码问题

**解决：**
- 从命令行启动程序，而不是双击
- 使用 PowerShell 或 CMD：
  ```
  cd "项目目录"
  python GUI.py
  ```

---

## 技术细节

### QNetworkProxy 代理类型

```python
# NoProxy：不使用任何代理，直接连接
proxy.setType(QtNetwork.QNetworkProxy.NoProxy)

# HttpProxy：使用 HTTP 代理
proxy.setType(QtNetwork.QNetworkProxy.HttpProxy)

# Socks5Proxy：使用 SOCKS5 代理
proxy.setType(QtNetwork.QNetworkProxy.Socks5Proxy)
```

### 为什么需要明确设置 NoProxy？

**原因：**
1. `setApplicationProxy()` 设置的是**全局代理**
2. 如果之前设置过代理，不清除会一直生效
3. 即使传入空字符串，也不会自动清除之前的设置
4. 必须**明确设置为 NoProxy** 才能清除代理

**类比：**
```python
# 错误做法
if not proxy_config:
    return  # ❌ 相当于"什么都不做"，旧设置仍然生效

# 正确做法
if not proxy_config:
    proxy.setType(QtNetwork.QNetworkProxy.NoProxy)  # ✅ 明确清除代理
    QtNetwork.QNetworkProxy.setApplicationProxy(proxy)
```

---

## 测试报告模板

测试完成后，请填写以下信息：

```
测试日期：____________________
测试环境：
  - 操作系统：Windows 10/11
  - Python 版本：____________
  - AnyConnect 版本：____________
  - VPN 连接状态：已连接 / 未连接

测试结果：
  [ ] 测试 1：Qt 代理设置验证 - 通过 / 失败
  [ ] 测试 2：配置文件修改 - 完成
  [ ] 测试 3：GUI 启动日志 - 正确 / 不正确
  [ ] 测试 4：自动登录功能 - 成功 / 失败

问题描述（如果有）：
________________________________
________________________________
________________________________

控制台日志（如果有问题）：
________________________________
________________________________
________________________________
```

---

## 回滚方案

如果修复后仍有问题，可以临时回滚到使用 Reqable：

```yaml
# config.yaml
proxies: "127.0.0.1:9000"  # 恢复 Reqable 代理
```

然后：
1. 启动 Reqable
2. 重启程序
3. 应该可以正常使用

---

## 总结

**关键修改：** 在 `_apply_proxy` 方法中，当 `proxies_config` 为空时，**明确设置为 NoProxy**，而不是直接返回。

**影响范围：** 仅影响 QWebEngineView（自动登录窗口），不影响 `requests` 库的连接。

**向后兼容：** 完全兼容，Reqable 代理模式仍然可以正常工作。

**测试状态：** Qt 代理设置测试通过 ✅

---

**修复版本：** v2.8.1
**修复日期：** 2025-10-24
**修复人：** Claude Code
