@echo off
chcp 65001 >nul
echo ===========================================
echo   OGG转MP3工具 - 轻量级快速安装（无FFmpeg）
echo ===========================================
echo.

echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python！请先安装Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
echo.

echo 🚀 使用国内镜像源安装依赖（推荐）...
echo.

echo 📦 安装GUI框架...
pip install -i https://mirrors.aliyun.com/pypi/simple/ customtkinter==5.2.2
pip install -i https://mirrors.aliyun.com/pypi/simple/ tkinterdnd2==0.3.0

echo.
echo 🎵 安装音频处理库（无需FFmpeg）...
pip install -i https://mirrors.aliyun.com/pypi/simple/ librosa
pip install -i https://mirrors.aliyun.com/pypi/simple/ soundfile

echo.
echo 🧪 测试安装结果...
python -c "import customtkinter, tkinterdnd2, librosa, soundfile; print('✅ 所有依赖安装成功！')"

if errorlevel 1 (
    echo.
    echo ⚠️  部分依赖安装失败，尝试备用镜像源...
    echo.
    
    echo 使用清华镜像源重试...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ customtkinter==5.2.2 tkinterdnd2==0.3.0 librosa soundfile
    
    echo.
    echo 再次测试...
    python -c "import customtkinter, tkinterdnd2, librosa, soundfile; print('✅ 备用方案安装成功！')"
    
    if errorlevel 1 (
        echo ❌ 安装失败，请检查网络连接或手动安装
        echo.
        echo 手动安装命令：
        echo pip install customtkinter tkinterdnd2 librosa soundfile
        pause
        exit /b 1
    )
)

echo.
echo ===========================================
echo ✅ 安装完成！特性说明：
echo.
echo 🎯 使用librosa + soundfile方案
echo 📁 无需下载FFmpeg（国内友好）
echo 🚀 高质量音频转换
echo 💾 体积小，速度快
echo.
echo 🎵 支持格式：OGG → MP3/WAV
echo ⚡ 纯Python实现，无外部依赖
echo.

echo 🚀 正在启动程序...
echo.
python ogg_to_mp3_converter.py

pause
