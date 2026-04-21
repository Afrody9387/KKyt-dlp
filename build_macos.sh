#!/bin/bash

# =================================================================
# KKyt-dlp macOS 一键打包构建脚本 (v1.6 最新方案)
# =================================================================
# 请确保当前系统已安装所需的依赖并处于项目的根目录下执行此脚本。
# 依赖环境: 
# 1. 位于 ./python 目录下的独立 Python 3.10 环境
# 2. 已通过 pip 安装 PyInstaller 和 dmgbuild
# =================================================================

# 1. 清理旧的构建文件
echo ">>> 清理旧的构建产物..."
rm -rf build/ dist/KKyt-dlp*
rm -f dist/KKyt-dlp*.dmg

# 2. PyInstaller 静态编译打包
echo ">>> 开始执行 PyInstaller 封包..."
# 关键修复说明：
# - 必须显式提取 --hidden-import PIL._tkinter_finder 与 PIL._imagingtk。
# - 原生源码中已废除 PIL 的 CTkImage 渲染，改用内部预缩放的 logo_48.png 及原生 tk.PhotoImage。
# - 必须通过 --add-data 将 logo_48.png、内部二进制(bin/*)关联进入 macOS bundle 中。
./python/bin/python3 -m PyInstaller \
  --noconfirm \
  --name "KKyt-dlp" \
  --windowed \
  --icon "logo.png" \
  --add-data "logo.png:." \
  --add-data "logo_48.png:." \
  --add-data "bin/yt-dlp:bin" \
  --add-data "bin/ffmpeg:bin" \
  --add-data "bin/ffprobe:bin" \
  --hidden-import PIL._tkinter_finder \
  --hidden-import PIL._imagingtk \
  main.py

if [ $? -ne 0 ]; then
    echo "❌ PyInstaller 打包失败！"
    exit 1
fi

echo "✅ App 封包完成，位置：dist/KKyt-dlp.app"

# 3. 构建 DMG 镜像
echo ">>> 开始执行 dmgbuild 构建原生免 AppleScript 镜像..."
# 采用 dmgbuild 可以有效绕开 AI/脚本 调起 create-dmg 所遭遇的 Mac 系统底层 Finder 权限屏蔽问题。
# 具体窗口、图标排版、无边框及隐形箭头特效均记录在 dmg_settings.py 中。
./python/bin/python3 -m dmgbuild -s dmg_settings.py "Install KKyt-dlp v1.6" dist/KKyt-dlp-v1.6-macOS.dmg

if [ $? -ne 0 ]; then
    echo "❌ dmgbuild 镜像构建失败！"
    exit 1
fi

echo "✅ DMG 镜像构建完成！最终发布文件位置："
echo "   $(pwd)/dist/KKyt-dlp-v1.6-macOS.dmg"
