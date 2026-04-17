<div align="center">
  <img src="logo.png" alt="KKyt-dlp Logo" width="128">
  <h1>KKyt-dlp</h1>
  <p>一个基于 yt-dlp 和 CustomTkinter 的极简、跨平台高清视频下载工具。</p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
  [![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-blue.svg)](README.md)
  [![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](requirements.txt)
</div>

---

## 🌟 项目简介

**KKyt-dlp** 旨在为普通用户提供最纯粹的视频下载体验。它屏蔽了命令行复杂的参数，将强大的 `yt-dlp` 内核包装在现代化、支持全系统暗色模式的图形界面（GUI）中。

### 核心特性
- **🚀 极速下载**：基于业界顶尖的 `yt-dlp` 内核，支持多线程加速。
- **🎨 现代 UI**：采用 `CustomTkinter` 设计，完美适配暗色/亮色模式。
- **🛡️ 纯净安全**：无广告、无多余进程、所有下载逻辑直接与官网交互。
- **💻 跨平台适配**：针对 Windows 的 CMD 窗口和 macOS 的 Tcl/Tk 崩溃问题均进行了专项深度优化。
- **🔧 智能内核管理**：内置 `n-challenge` 签名挑战解决方案（QuickJS），有效避免“格式不可用”报错。

---

## 📸 界面预览

*(此处可放置您的软件截图)*

---

## 📥 安装与运行

### 对于用户
- **Windows**: 下载并解压后，直接运行 `dist/KKyt-dlp.exe`。
- **macOS**: 获取 `.dmg` 安装镜像，将其拖入 `Applications` 文件夹即可使用。
  - *注意：首次打开可能需要右键点击选择“打开”以允许未签名应用。*

### 对于开发者 (本地运行)
1. 克隆仓库：
   ```bash
   git clone https://github.com/YourUsername/KKyt-dlp.git
   cd KKyt-dlp
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 初始化二进制内核 (ffmpeg/yt-dlp/qjs)：
   ```bash
   python setup_binaries.py
   ```
4. 启动程序：
   ```bash
   python main.py
   ```

---

## 🛠️ 打包指南

项目已预配置好双端打包 `.spec` 文件：

- **Windows**: 运行 `build_win.bat`。
- **macOS**: 建议使用独立 Python 环境以解决 Tcl/Tk 兼容性问题：
  ```bash
  python -m PyInstaller --noconfirm KKyt-dlp.spec
  ```

---

## 📜 开源协议

本项目基于 [MIT License](LICENSE) 协议开源。请务必遵守当地法律法规，仅限用于个人学习研究。

## 🙏 特别感谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的下载内核
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - 现代化的 UI 框架
