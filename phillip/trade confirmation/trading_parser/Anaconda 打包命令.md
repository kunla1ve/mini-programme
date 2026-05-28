根据您的需求，使用Python虚拟环境打包桌面上的 `trading_parser.py` 脚本为单个exe文件。以下是完整步骤：

## 1. 创建并激活虚拟环境

```bash
# 进入桌面目录
cd C:\Users\hongl\Desktop

# 创建虚拟环境
python -m venv trading_env

# 激活虚拟环境
trading_env\Scripts\activate
```

## 2. 安装必需的包（仅需要的）

```bash
# 升级pip
python -m pip install --upgrade pip

# 只安装必要的包
pip install pandas pyinstaller
```

## 3. 检查已安装的包

```bash
pip list
```
应该只显示：`pip`, `pandas`, `pyinstaller` 以及它们的依赖项。

## 4. 打包脚本

```bash
# 在激活的虚拟环境中执行打包
pyinstaller --onefile --console --exclude-module matplotlib --exclude-module numpy --exclude-module scipy trading_parser.py
```

## 5. 查找生成的exe文件

打包完成后，exe文件位于：
```
C:\Users\hongl\Desktop\dist\trading_parser.exe
```

## 完整的批处理脚本（可选）

创建一个 `build.bat` 文件在桌面上：

```batch
@echo off
cd /d C:\Users\hongl\Desktop

echo Creating virtual environment...
python -m venv trading_env

echo Activating virtual environment...
call trading_env\Scripts\activate.bat

echo Installing required packages...
pip install --upgrade pip
pip install pandas pyinstaller

echo Building executable...
pyinstaller --onefile --console --exclude-module matplotlib --exclude-module numpy --exclude-module scipy trading_parser.py

echo Build complete! Check the 'dist' folder.
pause
```

## 注意事項

- **确保在虚拟环境中执行打包**，这样只会包含必要的依赖
- `pandas` 会自动依赖 `numpy`，所以即使排除了 `numpy`，PyInstaller 可能仍会包含它
- 如果exe文件较大（50-100MB），这是因为 `pandas` 及其依赖本身就很大
- 测试exe文件时，建议先备份原脚本

## 测试exe

```bash
# 在命令行中测试
C:\Users\hongl\Desktop\dist\trading_parser.exe

# 或者
cd C:\Users\hongl\Desktop\dist
trading_parser.exe
```

如果需要减小exe大小，可以考虑使用 `--exclude` 排除更多不需要的模块，或者使用 UPX 压缩工具。
