# MUS Booking System - 独立可执行文件构建指南

## 📦 构建说明

本指南将帮助你将 MUS Booking System 打包成一个独立的可执行文件，可以在没有安装 Python 的电脑上运行。

---

## 🚀 快速开始

### Windows 用户

**最简单的方法：双击运行 `build.bat`**

```bash
# 直接双击 build.bat 文件
# 或在命令行中运行：
build.bat
```

脚本会自动完成以下操作：
1. 检查并安装 PyInstaller
2. 安装项目依赖
3. 清理旧的构建文件
4. 打包生成可执行文件
5. 打开输出文件夹

### 手动构建

如果你想手动控制构建过程：

```bash
# 1. 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 2. 运行 PyInstaller
pyinstaller build_standalone.spec --clean --noconfirm

# 3. 输出文件位于 dist/MUS_Booking/
```

---

## 📂 输出文件

构建完成后，你将在 `dist/MUS_Booking/` 文件夹中找到：

```
dist/MUS_Booking/
├── MUS_Booking.exe       # 主程序（双击运行）
├── resources/             # 资源文件
│   └── CCA.ico           # 程序图标
├── _internal/            # 运行时依赖（自动管理）
│   ├── PySide6/          # Qt 框架
│   ├── Python 运行时库
│   └── 其他依赖...
└── config.yaml           # 配置文件（首次运行自动生成）
```

**注意：**
- 整个 `dist/MUS_Booking/` 文件夹是一个完整的独立应用
- 必须保持文件夹结构完整
- 可以将整个文件夹压缩后发送给其他人

---

## 💡 使用方法

### 在本机使用

1. 打开 `dist/MUS_Booking/` 文件夹
2. 双击 `MUS_Booking.exe` 运行

### 分发给其他人

**方法 1：文件夹分发**
1. 将整个 `dist/MUS_Booking/` 文件夹压缩为 ZIP
2. 发送给其他人
3. 解压后运行 `MUS_Booking.exe`

**方法 2：创建安装包（可选）**
- 使用 Inno Setup 或 NSIS 创建安装程序
- 这样用户体��更好，但需要额外工具

---

## 📊 预期文件大小

根据配置，预期文件大小：

- **未优化**：约 200-300 MB
  - 包含完整的 PySide6 和 WebEngine

- **优化后**：约 100-150 MB
  - 排除了不必要的 Qt 模块
  - 启用了 UPX 压缩

- **进一步优化**：约 60-100 MB
  - 考虑移除 WebEngine（但会失去自动登录功能）
  - 使用更激进的排除策略

---

## 🔧 优化体积的方法

如果你觉得文件太大，可以尝试以下优化：

### 1. 移除自动登录功能（减少约 50MB）

编辑 `build_standalone.spec`，在 `excludes` 列表中添加：

```python
'PySide6.QtWebEngineWidgets',
'PySide6.QtWebEngineCore',
```

**注意**：这样会失去自动登录功能，需要手动粘贴 Cookie。

### 2. 启用 UPX 压缩

确保 `build_standalone.spec` 中的 `upx=True`（已默认启用）。

下载 UPX：
- 官网：https://upx.github.io/
- 将 `upx.exe` 添加到系统 PATH

### 3. 使用单文件模式（不推荐，启动较慢）

修改 `build_standalone.spec`：

```python
exe = EXE(
    ...,
    a.binaries,  # 添加这一行
    a.zipfiles,  # 添加这一行
    a.datas,     # 添加这一行
    ...
)

# 删除 COLLECT 部分
```

这会生成一个单独的 `.exe` 文件，但启动时需要解压到临时目录，启动较慢。

---

## ⚠️ 常见问题

### Q1: 构建失败，提示缺少模块

**解决方法：**
```bash
# 确保所有依赖已安装
pip install -r requirements.txt --upgrade

# 重新构建
build.bat
```

### Q2: 运行时提示缺少 DLL 文件

**解决方法：**
- 确保 Visual C++ Redistributable 已安装
- 下载地址：https://aka.ms/vs/17/release/vc_redist.x64.exe

### Q3: 文件太大，无法通过邮件发送

**解决方法：**
- 使用云盘（OneDrive、Google Drive、百度网盘等）
- 或使用压缩软件（7-Zip、WinRAR）进一步压缩

### Q4: 杀毒软件报毒

**解决方法：**
- 这是误报，PyInstaller 打包的程序经常被误报
- 添加信任/白名单
- 或使用代码签名证书（需要购买）

### Q5: 程序启动缓慢

**原因：**
- 首次启动时，程序需要解压和加载所有依赖
- 后续启动会快一些

**优化方法：**
- 使用文件夹模式（已默认，比单文件快）
- 将程序放在 SSD 硬盘上

---

## 🛠️ 技术细节

### PyInstaller 工作原理

1. **分析阶段**：扫描代码，识别所有导入的模块
2. **收集阶段**：收集所有 `.py` 文件、库文件、资源文件
3. **打包阶段**：
   - 编译 Python 代码为字节码
   - 将 Python 解释器嵌入
   - 打包所有依赖
4. **生成阶段**：生成可执行文件和支持文件

### 文件结构说明

```
dist/MUS_Booking/
├── MUS_Booking.exe           # Bootloader + 程序入口
└── _internal/                # 所有依赖和资源
    ├── base_library.zip      # Python 标准库
    ├── PySide6/              # Qt 框架
    │   ├── Qt6Core.dll       # Qt 核心
    │   ├── Qt6Gui.dll        # Qt GUI
    │   ├── Qt6Widgets.dll    # Qt 控件
    │   └── Qt6WebEngine*.dll # WebEngine（自动登录）
    ├── python3XX.dll         # Python 运行时
    └── 其他依赖库...
```

### 排除的模块

为了减小体积，以下模块已被排除：
- ❌ 测试框架（pytest, unittest）
- ❌ 文档工具（sphinx, docutils）
- ❌ 开发工具（setuptools, pip）
- ❌ 不使用的 Qt 模块（3D、Multimedia、Charts 等）
- ❌ 科学计算库（numpy, pandas, matplotlib）

---

## 📝 自定义构建

如果你需要自定义构建选项，可以编辑 `build_standalone.spec` 文件。

### 修改程序图标

```python
icon=r'path\to\your\icon.ico'
```

### 添加额外的资源文件

```python
datas = [
    ('path/to/file', 'destination'),
    ('path/to/folder', 'destination_folder'),
]
```

### 添加隐藏导入

```python
hiddenimports = [
    'your_module',
]
```

---

## 🎯 发布清单

发布给其他人之前，请确保：

- [ ] 程序能正常启动和运行
- [ ] 所有功能都正常工作（预订、自动登录、代理检测等）
- [ ] 配置文件能正常生成和保存
- [ ] 在没有 Python 的电脑上测试过
- [ ] 文件夹结构完整
- [ ] 附带了使用说明

---

## 📞 支持

如果遇到问题：
1. 查看构建日志（`build/MUS_Booking/warn-MUS_Booking.txt`）
2. 检查是否有报错信息
3. 参考 PyInstaller 官方文档：https://pyinstaller.org/

---

**祝构建顺利！🎉**
