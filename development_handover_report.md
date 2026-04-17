# KKyt-dlp 开发者变更与维护报告 (Windows 适配版)

本报告详细记录了在 Windows 环境下进行适配与打包过程中的所有关键代码变更，旨在为后续 macOS 版本的同步维护提供技术参考。

---

## 1. 核心下载引擎变更 (`downloader_engine.py`)

### 1.1 背景进程隐藏 (Windows 专用)
- **改动点**: 在所有 `subprocess.run` 和 `subprocess.Popen` 调用中注入了 `creationflags=0x08000000` (CREATE_NO_WINDOW)。
- **目的**: 彻底解决 Windows 端下载、更新或查询版本时频繁弹出黑色 CMD 窗口的问题。
- **兼容性**: 已通过 `if sys.platform == "win32"` 进行保护，不影响 macOS。

### 1.2 JavaScript 运行时 (QuickJS) 集成
- **改动点**: 
  - 引入了 `bin/qjs.exe` (QuickJS-ng)，并在 `ensure_binaries` 中加入同步逻辑。
  - 在下载命令中显式注入了 `--js-runtimes "quickjs:PATH_TO_QJS"`。
- **目的**: 解决 YouTube 最新的 `n-parameter` 签名挑战。没有此引擎会导致“格式不可用”报错。
- **Mac 维护建议**: macOS 通常自带或更易获取 JS 环境，如果不报 `n challenge` 错误，可不移植此部分。

### 1.3 极速启动模式 (性能优化)
- **改动点**: 移除了原有的 10 秒 `get-title` 预检逻辑。
- **目的**: 避免在处理复杂签名解密时界面长时间停在“获取信息”阶段。现在程序直接启动下载流，并从中实时解析标题。

### 1.4 手动 Cookie 导入逻辑
- **改动点**: 增加了对 `%APPDATA%/KKyt-dlp/cookies.txt` 的自动检测。
- **逻辑优先级**: `手动导入的文件` > `主页面浏览器选择`。
- **目的**: 绕过 Windows 端 Chromium 浏览器的数据库加密锁定 (DPAPI 错误)。

---

## 2. UI 界面与交互变更 (`main.py`)

### 2.1 任务栏与窗口图标修复
- **改动点**: 
  - 注入了 `ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID`。
  - 为主窗口和所有 `CTkToplevel` 子窗口增加了强制 `iconbitmap` 设置。
- **目的**: 解决 Windows 任务栏显示默认 Python 蓝色图标的问题。

### 2.2 设置页面扩展
- **功能新增**: 
  - **手动 Cookie 管理**: 增加了导入/清除 `cookies.txt` 的功能。
  - **核心插件更新**: 增加了调用 `yt-dlp -U` 的可视化按钮。
- **尺寸调整**: 设置窗口默认高度从 `450` 增加至 `620`。

### 2.3 文案调整
- 移除了关于页面中“macOS”的字样，修改为双端通用描述。

---

## 3. 打包配置变更 (`KKyt-dlp_Windows.spec`)

- **Datas 段**: 增加了 `('bin/qjs.exe', 'bin')`, `('logo.ico', '.')` 等关联。
- **Icon 配置**: 显式指定了 `icon=['logo.ico']`。
- **策略**: 将所有二进制文件通过 `datas` 关联，配合代码中的 `sys._MEIPASS` 释放逻辑，实现绿色免安装运行。

---

## 4. macOS 维护自检清单
如果您在 macOS 上重新打包发现异常，请检查：
1.  **路径**: 确保 `app_support_dir` 指向的是 `~/Library/Application Support/`。
2.  **二进制**: 替换 `bin/` 目录下的 `.exe` 为 macOS 版本的二进制文件。
3.  **权限**: macOS 的 `bin` 目录在释放后可能需要手动执行 `chmod +x`（代码中已包含此逻辑）。
4.  **Cookie**: 如果 Mac 端也遇到机器人拦截，可以复用我新写的“手动导入 cookies.txt”功能。

---
**报告整理人**: Antigravity (AI Coding Assistant)  
**日期**: 2026-04-16
