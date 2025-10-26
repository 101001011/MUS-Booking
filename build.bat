@echo off
chcp 65001 >nul
REM MUS Booking System - 构建独立可执行文件
REM 此脚本将项目打包成独立的 .exe 文件，包含所有依赖

echo ========================================
echo MUS Booking System - 独立可执行文件构建
echo ========================================
echo.

REM 检查 Python 是否已安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python！请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/5] 检查 PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] 正在安装 PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [错误] PyInstaller 安装失败！
        pause
        exit /b 1
    )
)
echo [OK] PyInstaller 已准备就绪

echo.
echo [2/5] 检查项目依赖...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [警告] 依赖安装可能不完整，但继续构建...
)
echo [OK] 依赖已准备就绪

echo.
echo [3/5] 清理旧的构建文件...
if exist "dist\MUS_Booking" (
    echo 删除旧的 dist\MUS_Booking 目录...
    rmdir /s /q "dist\MUS_Booking"
)
if exist "build" (
    echo 删除旧的 build 目录...
    rmdir /s /q "build"
)
echo [OK] 清理完成

echo.
echo [4/5] 开始构建（这可能需要几分钟）...
echo 请稍候...
pyinstaller build_standalone.spec --clean --noconfirm
if %errorlevel% neq 0 (
    echo [错误] 构建失败！请检查错误信息。
    pause
    exit /b 1
)
echo [OK] 构建完成

echo.
echo [5/5] 检查输出文件...
if exist "dist\MUS_Booking\MUS_Booking.exe" (
    echo [成功] ✓ 可执行文件已生成！
    echo.
    echo 输出位置：dist\MUS_Booking\
    echo 主��序：dist\MUS_Booking\MUS_Booking.exe
    echo.
    echo 您可以将整个 dist\MUS_Booking 文件夹发送给其他人使用。
    echo 双击 MUS_Booking.exe 即可运行，无需安装 Python。
    echo.

    REM 显示文件大小
    for %%I in ("dist\MUS_Booking") do (
        echo 文件夹大小：约 %%~zI 字节
    )

    echo.
    echo 按任意键打开输出文件夹...
    pause >nul
    explorer "dist\MUS_Booking"
) else (
    echo [错误] 未找到输出文件！构建可能失败。
    pause
    exit /b 1
)

echo.
echo ========================================
echo 构建完成！
echo ========================================
