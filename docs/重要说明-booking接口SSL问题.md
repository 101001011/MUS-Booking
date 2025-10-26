# 重要说明 - booking.cuhk.edu.cn SSL 握手问题

## 问题现状

经过详细测试和诊断，发现以下情况：

### ✅ 已成功修复

**QWebEngineView（自动登录窗口）** 现在可以直接通过 AnyConnect VPN 访问学校网站：
- ✅ 成功获取 Cookie
- ✅ 可以正常登录
- ✅ 不需要 Reqable 代理

### ❌ 仍存在问题

**booking.cuhk.edu.cn 的预订接口** 无法通过 Python requests 库直接连接：
- ❌ SSL 握手失败（SSLV3_ALERT_HANDSHAKE_FAILURE）
- ❌ 即使禁用 SSL 验证（verify=False）仍然失败
- ❌ 即使 AnyConnect VPN 已连接仍然无法访问

## 技术分析

### 测试结果

```python
# 测试：直接连接 booking.cuhk.edu.cn
# 结果：SSL握手失败

[FAIL] 请求失败
异常类型: SSLError
异常信息: HTTPSConnectionPool(host='booking.cuhk.edu.cn', port=443):
         Max retries exceeded with url: /
         (Caused by SSLError(SSLError(1, '[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE]
         sslv3 alert handshake failure (_ssl.c:1002)')))
```

### 为什么会这样？

1. **QWebEngineView 可以连接**
   - 使用 Chromium 的网络栈
   - 支持更多的 SSL/TLS 版本和密码套件
   - SSL 协商能力更强

2. **Python requests 无法连接**
   - 使用 urllib3 + OpenSSL
   - 可能不支持服务器要求的 SSL/TLS 配置
   - SSL 握手失败

3. **通过 Reqable 可以连接**
   - Reqable 作为中间代理
   - 使用自己的 SSL 栈处理连接
   - 绕过了 Python requests 的 SSL 限制

## 可能的原因

1. **服务器 SSL 配置特殊**
   - booking.cuhk.edu.cn 可能使用了较旧或较新的 TLS 版本
   - 或者要求特定的密码套件

2. **客户端证书要求**
   - 服务器可能需要特定的客户端证书
   - 浏览器有，但 Python requests 没有

3. **SNI 或其他 TLS 扩展**
   - 服务器可能依赖特定的 TLS 扩展
   - Python requests 可能不支持

## 解决方案

### 方案 1：继续使用 Reqable（推荐）

这是目前最可靠的方案：

**使用场景：**
1. **自动登录** → AnyConnect VPN（直接连接）✅
2. **预订请求** → Reqable 代理 ✅

**配置：**
```yaml
# config.yaml
proxies: "127.0.0.1:9000"  # 使用 Reqable 代理
```

**使用步骤：**
1. 打开 AnyConnect 并连接
2. 打开 Reqable（端口 9000）
3. 启动程序
4. 点击"自动登录获取Cookie" → 成功（通过 VPN 直接连接）✅
5. 点击"开始"预订 → 成功（通过 Reqable 代理）✅

**优点：**
- ✅ 稳定可靠
- ✅ 已验证可行
- ✅ 自动登录更快（直接连接）
- ✅ 预订请求成功（通过代理）

**缺点：**
- ⚠️ 需要同时运行 AnyConnect 和 Reqable

---

### 方案 2：尝试修复 SSL 配置（实验性）

可以尝试配置 Python requests 使用不同的 SSL 设置，但**不保证成功**。

**可能的尝试：**
1. 强制使用 TLSv1.2 或 TLSv1.3
2. 配置特定的密码套件
3. 使用系统 CA 证书
4. 自定义 SSL 上下文

**风险：**
- 可能仍然无法解决问题
- 需要大量调试
- 可能影响稳定性

---

### 方案 3：仅在校园网内使用（受限）

如果在校园网内，可能可以直接连接：

**配置：**
```yaml
proxies: ""  # 不使用代理
```

**限制：**
- 仅在校园网内可用
- 校园外必须使用方案 1

---

## 推荐配置

### 标准配置（AnyConnect + Reqable）

```yaml
# config.yaml
proxies: "127.0.0.1:9000"  # 使用 Reqable 代理

user_id: "您的学号"
user_password: "您的密码"
user_name: "您的姓名"
user_email: "您的邮箱"
user_phone: "您的电话"

# 其他配置...
```

**使用流程：**
```
1. 打开 AnyConnect → 连接到学校 VPN
2. 打开 Reqable → 确保端口 9000 正常运行
3. 运行程序：python GUI.py
4. 自动登录获取 Cookie（通过 VPN 直接连接）
5. 开始预订（通过 Reqable 代理）
```

---

## 详细对比

| 功能 | 原方案 | 修复后 |
|-----|--------|--------|
| 自动登录 | 通过 Reqable | ✅ 直接通过 VPN |
| 预订请求 | 通过 Reqable | ⚠️ 仍需 Reqable |
| 需要 Reqable | 是 | 是（仅预订） |
| 需要 VPN | 是 | 是 |

---

## 技术细节：SSL 握手失败

### 完整错误堆栈

```
ssl.SSLError: [SSL: SSLV3_ALERT_HANDSHAKE_FAILURE]
              sslv3 alert handshake failure (_ssl.c:1002)
```

### 这意味着什么？

1. **客户端（Python）发起 SSL 握手**
2. **服务器（booking.cuhk.edu.cn）拒绝握手**
   - 可能是：不支持客户端提供的 TLS 版本
   - 或者：不支持客户端提供的密码套件
   - 或者：需要客户端证书

3. **握手失败，连接终止**

### 为什么浏览器可以？

- Chromium/Chrome 支持更广泛的 SSL/TLS 配置
- 有更智能的协商算法
- 可能有学校的客户端证书（如果需要）

### 为什么 Reqable 可以？

- Reqable 作为中间人，建立两个独立的 SSL 连接：
  1. Python → Reqable（使用 Python 可以接受的 SSL）
  2. Reqable → booking.cuhk.edu.cn（使用服务器要求的 SSL）
- 这样绕过了 Python requests 的限制

---

## 总结

### 当前状态

✅ **部分成功：** 自动登录不再需要 Reqable
⚠️ **仍需改进：** 预订请求仍需 Reqable

### 最佳实践

1. **使用 AnyConnect + Reqable 组合**
2. **自动登录** 通过 VPN 直接连接（更快）
3. **预订请求** 通过 Reqable 代理（稳定）

### 长期方案

如果想完全不使用 Reqable，需要：
1. 联系学校 IT 部门了解 booking.cuhk.edu.cn 的 SSL 配置要求
2. 或者使用更底层的 SSL 库（如 pyOpenSSL）自定义配置
3. 或者在校园网内直接使用（但这限制了使用场景）

---

**版本：** v2.8.2
**更新日期：** 2025-10-24
**状态：** 部分修复，需继续使用 Reqable 进行预订
