# -*- coding: utf-8 -*-
"""
打包脚本 - 带详细进度和错误信息
Created on Mon May 18 17:28:20 2026
"""

import subprocess
import sys
import os
from pathlib import Path
import time

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_progress(text):
    print(f"[{time.strftime('%H:%M:%S')}] {text}")

def run_command(cmd, description):
    """运行命令并实时显示输出"""
    print_progress(f"开始: {description}")
    print(f"命令: {' '.join(cmd)}")
    print("-" * 70)
    
    # 实时显示输出
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    output_lines = []
    for line in process.stdout:
        print(line, end='')
        output_lines.append(line)
    
    process.wait()
    
    if process.returncode == 0:
        print_progress(f"✓ 完成: {description}")
    else:
        print_progress(f"✗ 失败: {description} (返回码: {process.returncode})")
    
    return process.returncode, ''.join(output_lines)

def main():
    print_header("PyInstaller 打包工具 - 详细日志模式")
    
    # 切换到脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print_progress(f"工作目录: {script_dir}")
    
    # 检查源文件
    source_file = script_dir / "trading_parser.py"
    if not source_file.exists():
        print(f"\n❌ 错误: 找不到 {source_file}")
        print("请确保 trading_parser.py 在当前目录")
        return
    
    print_progress(f"源文件: {source_file}")
    print_progress(f"文件大小: {source_file.stat().st_size} bytes")
    
    # 检查 Python 环境
    print_progress(f"Python: {sys.executable}")
    print_progress(f"Python 版本: {sys.version}")
    
    # 步骤1: 检查/安装必要的包
    print_header("步骤 1/3: 检查依赖包")
    
    packages = ['pyinstaller', 'openpyxl']
    for package in packages:
        print_progress(f"检查 {package}...")
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', package],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print_progress(f"⚠ {package} 未安装，正在安装...")
            install_result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package],
                capture_output=True,
                text=True
            )
            if install_result.returncode == 0:
                print_progress(f"✓ {package} 安装成功")
            else:
                print(f"✗ {package} 安装失败:")
                print(install_result.stderr)
                return
        else:
            print_progress(f"✓ {package} 已安装")
    
    # 步骤2: 清理旧的打包文件
    print_header("步骤 2/3: 清理旧文件")
    
    folders_to_remove = ['build', 'dist']
    for folder in folders_to_remove:
        folder_path = script_dir / folder
        if folder_path.exists():
            print_progress(f"删除 {folder_path}...")
            import shutil
            try:
                shutil.rmtree(folder_path)
                print_progress(f"✓ 已删除 {folder}")
            except Exception as e:
                print_progress(f"⚠ 删除 {folder} 时出错: {e}")
    
    spec_file = script_dir / "trading_parser.spec"
    if spec_file.exists():
        try:
            spec_file.unlink()
            print_progress("✓ 已删除 .spec 文件")
        except:
            pass
    
    # 步骤3: 打包
    print_header("步骤 3/3: 开始打包（可能需要 2-3 分钟）")
    print_progress("提示: pandas 已被移除，打包速度应该很快")
    print_progress("如果看到 'Building EXE' 说明正在生成 exe 文件")
    print()
    
    # 使用 PyInstaller 命令
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',           # 打包成单个文件
        '--console',           # 控制台程序
        '--name', '交易記錄轉換工具',  # 程序名称
        '--clean',             # 清理临时文件
        '--noconfirm',         # 覆盖输出目录
        '--log-level=DEBUG',   # 详细日志
        '--hidden-import=openpyxl',
        '--hidden-import=openpyxl.cell',
        '--hidden-import=openpyxl.reader',
        '--hidden-import=openpyxl.worksheet',
        str(source_file)
    ]
    
    start_time = time.time()
    returncode, output = run_command(cmd, "PyInstaller 打包")
    elapsed_time = time.time() - start_time
    
    # 结果处理
    print_header("打包结果")
    print(f"耗时: {elapsed_time:.1f} 秒")
    
    if returncode == 0:
        exe_path = script_dir / "dist" / "交易記錄轉換工具.exe"
        if exe_path.exists():
            file_size = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n✅ 打包成功！")
            print(f"   文件位置: {exe_path}")
            print(f"   文件大小: {file_size:.1f} MB")
            print("\n   可以直接双击运行测试")
            
            # 可选：复制到桌面
            desktop = Path.home() / "Desktop"
            desktop_exe = desktop / "交易記錄轉換工具.exe"
            try:
                import shutil
                shutil.copy2(exe_path, desktop_exe)
                print(f"   ✓ 已复制到桌面: {desktop_exe}")
            except Exception as e:
                print(f"   ⚠ 复制到桌面失败: {e}")
        else:
            print("\n❌ 找不到生成的 exe 文件")
            print("   请检查 dist 文件夹")
    else:
        print(f"\n❌ 打包失败 (返回码: {returncode})")
        print("\n常见问题排查:")
        print("1. 检查 trading_parser.py 是否有语法错误")
        print("2. 尝试手动运行: pyinstaller --onefile trading_parser.py")
        print("3. 确保 openpyxl 已正确安装")
        
        # 检查是否有明显的错误信息
        if "No module named" in output:
            print("\n提示: 缺少某个模块，请安装后重试")
        if "Permission denied" in output:
            print("\n提示: 权限不足，请以管理员身份运行")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断打包")
    except Exception as e:
        print(f"\n❌ 未预期的错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n" + "=" * 70)
        input("按 Enter 键退出...")
