# -*- coding: utf-8 -*-
"""
Created on Mon May 18 17:28:20 2026

@author: hongl
"""

import subprocess
import sys
import os

os.chdir(r'C:\Users\hongl\Desktop')

print("正在打包，请耐心等待1-2分钟...")
print("="*60)

# 直接用 Python 模块方式运行
result = subprocess.run(
    [sys.executable, '-m', 'PyInstaller', 
     '--onefile', '--console', 
     '--name', '交易記錄轉換工具', 
     '--clean', 'trading_parser.py'],
    shell=True
)

print("="*60)
if result.returncode == 0:
    print("\n✅ 打包成功！")
    exe_path = r"C:\Users\hongl\Desktop\dist\交易記錄轉換工具.exe"
    if os.path.exists(exe_path):
        print(f"程序位置：{exe_path}")
        print("可以直接双击运行！")
else:
    print("\n❌ 打包失败")