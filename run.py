# -*- coding: utf-8 -*-
"""
MUS Booking System - 程序入口
Version: 2.10.0

使用方法:
    python run.py
"""

import sys
import os

# 将 src 目录添加到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# 导入并运行主程序
if __name__ == "__main__":
    # 导入主窗口模块（使用重构后的模块化结构）
    from main_window import main

    # 运行主程序
    main()
