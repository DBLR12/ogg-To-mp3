@echo off
chcp 65001 >nul
echo =================================
echo    OGG转MP3转换工具 安装脚本
echo =================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境!
    echo 请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python环境检查通过!
echo.

echo 正在安装依赖包...
echo.
echo 🚀 使用国内镜像源快速安装（推荐方案）...
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple customtkinter==5.2.2 tkinterdnd2==0.3.0
echo.
echo 🎵 安装音频处理库（无需FFmpeg）...
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple librosa soundfile
if errorlevel 1 (
    echo.
    echo ⚠️  librosa安装失败，尝试备用方案...
    echo 正在安装pydub（需要FFmpeg）...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pydub
    if errorlevel 1 (
        echo.
        echo ⚠️  所有音频库安装失败，尝试轻量级方案...
        pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mutagen
    )
)

echo.
echo 正在检查ffmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  未检测到FFmpeg，程序可能无法正常工作
    echo.
    echo 🔧 FFmpeg安装方法:
    echo    1. 推荐: 使用 winget install ffmpeg
    echo    2. 手动下载: https://www.gyan.dev/ffmpeg/builds/
    echo    3. 解压后将bin目录添加到系统PATH环境变量
    echo.
    echo 💡 继续运行程序，转换时会提示FFmpeg相关问题
    echo.
) else (
    echo ✅ FFmpeg 已安装
)
echo.

echo 安装完成! 正在启动程序...
echo.
python ogg_to_mp3_converter.py

pause
