import os
import sys
import threading
import psutil
import subprocess
import re
import json
import shutil
import platform

class DownloadTask:
    """单个下载任务的逻辑处理类"""
    def __init__(self, url, quality="best", cookies_browser=None, download_path=None, video_format="mp4"):
        self.url = url
        self.quality = quality
        self.cookies_browser = cookies_browser
        self.download_path = download_path or os.path.expanduser("~/Downloads")
        self.video_format = video_format.lower()
        
        # 针对不同操作系统的持久化路径
        if sys.platform == "win32":
            self.app_support_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "KKyt-dlp")
        else:
            # macOS / Linux
            self.app_support_dir = os.path.expanduser("~/Library/Application Support/KKyt-dlp")
            
        self.persistent_bin_dir = os.path.join(self.app_support_dir, "bin")
        self.manual_cookies_path = os.path.join(self.app_support_dir, "cookies.txt")
        
        # 任务属性（对应 UI 显示）
        self.status = "等待中"
        self.progress = 0
        self.speed = "0B/s"
        self.eta = "00:00"
        self.title = "正在获取视频信息..."
        self.filename = ""
        
        self.stop_event = threading.Event()
        self._thread = None
        self.error = None
        self._process = None # 记录子进程

    def get_bin_path(self, bin_name):
        """获取二进制文件路径：优先使用持久化路径，其次使用包内路径"""
        # 兼容 Windows 扩展名
        if sys.platform == "win32" and not bin_name.endswith(".exe"):
            bin_name += ".exe"
            
        # 1. 检查持久化路径 (Application Support / APPDATA)
        persistent_path = os.path.join(self.persistent_bin_dir, bin_name)
        if os.path.exists(persistent_path):
            return persistent_path
            
        # 2. 如果包内有备份，则复制到持久化路径并返回 (Seeding 种子逻辑)
        return self._seed_binary(bin_name)
        
    def _seed_binary(self, bin_name):
        """内部种子复制逻辑"""
        persistent_path = os.path.join(self.persistent_bin_dir, bin_name)
        if hasattr(sys, '_MEIPASS'):
            bundled_path = os.path.join(sys._MEIPASS, "bin", bin_name)
            if os.path.exists(bundled_path):
                try:
                    os.makedirs(self.persistent_bin_dir, exist_ok=True)
                    shutil.copy2(bundled_path, persistent_path)
                    os.chmod(persistent_path, 0o755)
                    return persistent_path
                except:
                    return bundled_path
        
        # 本地开发路径
        local_bin = os.path.abspath(os.path.join(os.path.dirname(__file__), "bin", bin_name))
        return local_bin if os.path.exists(local_bin) else bin_name

    def run(self):
        """线程内部运行的下载逻辑：改为『直接启动 -> 实时解析』极速模式"""
        ytdlp_bin = self.get_bin_path("yt-dlp")
        ffmpeg_bin = self.get_bin_path("ffmpeg")
        qjs_bin = self.get_bin_path("qjs")
        
        # 1. 立即设置状态，不再进行 10s 预检，防止界面卡在“获取信息”
        self.status = "准备开始..."
        
        # 2. 构建正式下载命令
        cmd = [
            ytdlp_bin,
            "--no-config",
            "--no-check-certificates",
            "--no-playlist",
            "--newline",
            "--progress",
            "--progress-template", "%(progress._percent_str)s | %(progress._speed_str)s | %(progress._eta_str)s",
            "--print", "after_move:filename",
            "-o", os.path.join(self.download_path, "%(title)s.%(ext)s"),
            "--ffmpeg-location", os.path.dirname(ffmpeg_bin)
        ]
        
        # 注入客户端伪装参数 (2026 最稳策略)
        cmd.extend(["--extractor-args", "youtube:player_client=web_safari"])
        
        # 显式指定 JS 运行时 (解决 n-challenge 失败问题)
        cmd.extend(["--js-runtimes", f"quickjs:{qjs_bin}"])
        
        # 优先使用手动导入的 Cookie
        if os.path.exists(self.manual_cookies_path):
            cmd.extend(["--cookies", self.manual_cookies_path])
        # 其次使用浏览器 Cookie
        elif self.cookies_browser and self.cookies_browser != "None":
            cmd.extend(["--cookies-from-browser", self.cookies_browser.lower()])
        
        # 环境准备：将 qjs 目录加入 PATH (双重保险)
        env = os.environ.copy()
        bin_dir = os.path.dirname(qjs_bin)
        if bin_dir not in env.get("PATH", ""):
            env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
        
        # 逻辑：智能自动重命名 (如果文件已存在，yt-dlp 默认会跳过，我们这里通过更改模板或让其强制覆盖)
        # 实际上 yt-dlp 并不支持简单的 "如果存在则重命名" 模板。
        # 最简单的方法是使用 --no-overwrites 并检测。或者使用 %(id)s
        # 用户要求的是“序号”，所以我们在 -o 这里手动指定。
        
        # 如果我们已经拿到了标题，我们可以尝试手动解决冲突
        if self.title and self.title != "正在获取视频信息...":
            # 预测后缀 (根据 video_format 或 quality)
            ext = "mp4" if self.video_format == "mp4" else "webm"
            if self.quality == "Audio Only": ext = "mp3"
            
            base_filename = f"{self.title}.{ext}"
            final_path = os.path.join(self.download_path, base_filename)
            
            # 手动序号递增逻辑
            count = 1
            while os.path.exists(final_path):
                new_filename = f"{self.title} ({count}).{ext}"
                final_path = os.path.join(self.download_path, new_filename)
                count += 1
            
            # 强制使用该路径
            cmd[cmd.index("-o") + 1] = final_path

        # 画质与格式逻辑
        if self.quality == "Audio Only":
            cmd.extend(["-x", "--audio-format", "mp3"])
        elif self.video_format == "mp4":
            cmd.extend(["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"])
            cmd.extend(["--merge-output-format", "mp4"])
        elif self.video_format == "webm":
            cmd.extend(["-f", "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best"])
            cmd.extend(["--merge-output-format", "webm"])
        elif self.video_format == "mkv":
            cmd.extend(["-f", "bestvideo+bestaudio/best"])
            cmd.extend(["--merge-output-format", "mkv"])
        elif self.video_format == "mov":
            cmd.extend(["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"])
            cmd.extend(["--merge-output-format", "mov"])
        else:
            mapping = {
                "Best": "bestvideo+bestaudio/best",
                "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]"
            }
            cmd.extend(["-f", mapping.get(self.quality, "bestvideo+bestaudio/best")])
        
        # 环境准备：将 qjs 目录加入 PATH
        env = os.environ.copy()
        bin_dir = os.path.dirname(qjs_bin)
        if bin_dir not in env.get("PATH", ""):
            env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")

        try:
            self.status = "准备开始..."
            # 针对 Windows 隐藏黑窗口
            creationflags = 0x08000000 if sys.platform == "win32" else 0
            
            self._process = subprocess.Popen(
                cmd + [self.url], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=creationflags,
                env=env
            )
            
            for line in self._process.stdout:
                if self.stop_event.is_set():
                    self._process.terminate()
                    break
                
                line = line.strip()
                if not line: continue
                
                # 查重逻辑检测（兜底，如果手动预检没生效）
                if "has already been downloaded" in line:
                    self.status = "已完成(已存在)"
                    self.progress = 100
                    continue

                if "Destination:" in line:
                    dest_title = os.path.basename(line.split("Destination:")[1].strip())
                    if "正在获取" in self.title:
                        self.title = dest_title
                
                if "|" in line and "%" in line:
                    parts = line.split("|")
                    if len(parts) >= 3:
                        try:
                            self.status = "正在下载"
                            self.progress = float(parts[0].replace("%", "").strip())
                            self.speed = parts[1].strip()
                            self.eta = parts[2].strip()
                        except:
                            pass
                
                if os.path.exists(line) and not line.endswith(".part") and "/" in line:
                    self.filename = line
                    self.title = os.path.basename(line)

            stderr_output = self._process.stderr.read()
            if self._process.wait() != 0 and not self.stop_event.is_set():
                raise Exception(stderr_output or "未知下载错误")
                
            if self.status != "已完成(已存在)":
                self.status = "下载完成"
        except Exception as e:
            if self.stop_event.is_set():
                self.status = "已停止"
            else:
                self.status = "发生错误"
                error_msg = str(e)
                # 更加鲁棒的错误识别：只要包含 cookie 和 copy/database/lock/permission 等关键字，就指引用户关闭浏览器
                low_err = error_msg.lower()
                if "confirm you are not a bot" in low_err:
                    self.error = "验证码拦截: YouTube 触发了人机验证。请在‘Cookie 获取’中选择一个已登录的浏览器（建议 Edge），并 [必须完全关闭] 该浏览器后重试。"
                elif "dpapi" in low_err:
                    self.error = "浏览器加密错误 (DPAPI): 无法解密浏览器的 Cookie 数据。这通常是由于浏览器更新导致的协议冲突。 \n\n建议: \n1. 点击程序右上角 [设置] -> [检查并更新核心插件] 尝试升级解决。\n2. 若升级无效，请尝试在‘Cookie 获取’中选择‘不使用’并重试。"
                elif "cookie" in low_err and ("copy" in low_err or "database" in low_err or "lock" in low_err or "permission" in low_err):
                    # 提示用户关闭浏览器，并解释 Chrome/Edge 的通用性
                    self.error = "浏览器占用: 无法读取 Cookie 数据。请先 [完全关闭] 您的浏览器（Edge/Chrome等），然后点击重试。 \n\n(注: Edge 报错可能显示为 Chrome，均需关闭浏览器解锁数据)"
                elif "unsupported url" in low_err:
                    self.error = "不支持的链接: 暂不支持此平台或链接格式错误，请检查后再试。"
                else:
                    self.error = f"下载错误: {error_msg}"
                print(f"执行报错: {error_msg}")

    def start(self):
        """启动下载线程"""
        self.stop_event.clear()
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self):
        """停止下载并清理残留进程"""
        self.stop_event.set()
        self.status = "正在停止..."
        if self._process:
            try:
                self._process.terminate()
            except:
                pass
        self.cleanup_processes()

    def cleanup_processes(self):
        """杀掉残留子进程"""
        try:
            current_process = psutil.Process()
            children = current_process.children(recursive=True)
            for child in children:
                try:
                    name = child.name().lower()
                    if any(x in name for x in ['ffmpeg', 'ffprobe', 'yt-dlp']):
                        child.kill()
                except: pass
        except: pass

class DownloaderEngine:
    """下载引擎管理类"""
    def __init__(self):
        self.tasks = []
        # 针对 macOS 的持久化二进制路径: ~/Library/Application Support/KKyt-dlp/bin
        self.app_support_dir = os.path.expanduser("~/Library/Application Support/KKyt-dlp")
        self.persistent_bin_dir = os.path.join(self.app_support_dir, "bin")
        self.last_error = ""

    def add_task(self, url, quality, cookies_browser, download_path=None, video_format="mp4"):
        """创建并初始化一个下载阶段"""
        task = DownloadTask(url, quality, cookies_browser, download_path, video_format)
        self.tasks.append(task)
        return task

    def ensure_binaries(self):
        """确保二进制文件已同步到持久化目录"""
        for bin_name in ["yt-dlp", "ffmpeg", "qjs"]:
            persistent_path = os.path.join(self.persistent_bin_dir, bin_name)
            # 兼容 Windows
            if sys.platform == "win32" and not persistent_path.endswith(".exe"):
                persistent_path += ".exe"
                
            if not os.path.exists(persistent_path):
                self._seed_binary(bin_name)
        
        # Windows 特供：创建一个 quickjs.exe 副本以防某些版本只认这个名字
        if sys.platform == "win32":
            qjs_path = os.path.join(self.persistent_bin_dir, "qjs.exe")
            quickjs_path = os.path.join(self.persistent_bin_dir, "quickjs.exe")
            if os.path.exists(qjs_path) and not os.path.exists(quickjs_path):
                try:
                    shutil.copy2(qjs_path, quickjs_path)
                except: pass

    def _seed_binary(self, bin_name):
        """内部种子复制逻辑"""
        persistent_path = os.path.join(self.persistent_bin_dir, bin_name)
        if hasattr(sys, '_MEIPASS'):
            bundled_path = os.path.join(sys._MEIPASS, "bin", bin_name)
            if os.path.exists(bundled_path):
                try:
                    os.makedirs(self.persistent_bin_dir, exist_ok=True)
                    shutil.copy2(bundled_path, persistent_path)
                    os.chmod(persistent_path, 0o755)
                    return persistent_path
                except:
                    return bundled_path
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "bin", bin_name))

    def get_bin_path(self, bin_name):
        """通用路径获取：优先持久化"""
        persistent_path = os.path.join(self.persistent_bin_dir, bin_name)
        if os.path.exists(persistent_path):
            return persistent_path
        return self._seed_binary(bin_name)

    def update_core(self):
        """更新外置 yt-dlp 插件"""
        self.ensure_binaries()
        ytdlp_bin = self.get_bin_path("yt-dlp")
        self.last_error = ""
        try:
            # 针对 Windows 隐藏黑窗口
            creationflags = 0x08000000 if sys.platform == "win32" else 0
            # 运行 yt-dlp -U 命令
            result = subprocess.run([ytdlp_bin, "-U"], capture_output=True, text=True, creationflags=creationflags)
            if result.returncode == 0:
                if "is up to date" in result.stdout:
                    return "LATEST"
                return True
            else:
                self.last_error = result.stderr or result.stdout
                return False
        except Exception as e:
            self.last_error = str(e)
            return False

    def get_version(self):
        """获取外置二进制版本"""
        # 获取版本前也确保文件存在，否则会报错
        self.ensure_binaries()
        ytdlp_bin = self.get_bin_path("yt-dlp")
        # 针对 Windows 隐藏黑窗口
        creationflags = 0x08000000 if sys.platform == "win32" else 0
        try:
            env = os.environ.copy()
            ytdlp_dir = os.path.dirname(ytdlp_bin)
            if ytdlp_dir not in env.get("PATH", ""):
                env["PATH"] = ytdlp_dir + os.pathsep + env.get("PATH", "")
                
            result = subprocess.run([ytdlp_bin, "--version"], capture_output=True, text=True, creationflags=creationflags, env=env)
            return result.stdout.strip()
        except:
            return "未知版本"
