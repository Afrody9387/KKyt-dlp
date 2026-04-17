import os
import sys
import tkinter as tk
import customtkinter as ctk
import subprocess
from tkinter import messagebox
from PIL import Image
from downloader_engine import DownloaderEngine, DownloadTask
from config_manager import ConfigManager

# 基础 UI 设置
ctk.set_appearance_mode("Light")  # 默认明亮模式
ctk.set_default_color_theme("blue")

class DownloadItem(ctk.CTkFrame):
    """单个下载任务的卡片组件"""
    def __init__(self, master, task, remove_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.task = task
        self.remove_callback = remove_callback

        self.grid_columnconfigure(0, weight=1)
        self.configure(fg_color="#F8F9FA", corner_radius=12, border_width=1, border_color="#E0E0E0")

        # 视频标题
        self.title_label = ctk.CTkLabel(self, text=self.task.title, font=("Microsoft YaHei", 14, "bold"), anchor="w")
        self.title_label.grid(row=0, column=0, padx=15, pady=(12, 0), sticky="ew")

        # 实时数据 (下载速度 / 剩余时间)
        self.stats_label = ctk.CTkLabel(self, text="", font=("Microsoft YaHei", 12), text_color="#666666")
        self.stats_label.grid(row=0, column=1, padx=15, pady=(12, 0), sticky="e")

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(self, height=8, corner_radius=4)
        self.progress_bar.grid(row=1, column=0, columnspan=2, padx=15, pady=12, sticky="ew")
        self.progress_bar.set(0)

        # 底部控制区
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 12), sticky="ew")

        # 任务状态文字
        self.status_label = ctk.CTkLabel(self.btn_frame, text=self.task.status, font=("Microsoft YaHei", 12))
        self.status_label.pack(side="left")

        # 功能按钮
        self.delete_btn = ctk.CTkButton(self.btn_frame, text="删除", width=60, height=28, 
                                        fg_color="#FF4D4D", hover_color="#CC0000", command=self.delete)
        self.delete_btn.pack(side="right", padx=5)

        self.stop_btn = ctk.CTkButton(self.btn_frame, text="停止", width=60, height=28, 
                                      fg_color="#FFA500", hover_color="#CC8400", command=self.stop)
        self.stop_btn.pack(side="right", padx=5)

        self.start_btn = ctk.CTkButton(self.btn_frame, text="开始", width=60, height=28, 
                                       command=self.start)
        self.start_btn.pack(side="right", padx=5)

        # 启动 UI 轮询更新
        self.update_ui()

    def start(self):
        """开始下载任务"""
        if self.task.status in ["等待中", "已停止", "发生错误"]:
            self.task.start()
            self.start_btn.configure(text="启动中...", state="disabled")
            self.status_label.configure(text="启动中...", text_color="#333333")
            self.update_ui()

    def stop(self):
        """停止下载任务"""
        # 允许在任何活跃状态下停止，包括等待和启动中
        if self.task.status not in ["下载完成", "发生错误", "已停止"]:
            self.task.stop()
            self.stop_btn.configure(text="停止中...", state="disabled")
            self.status_label.configure(text="正在停止...", text_color="#666666")
            self.update_ui()

    def open_folder(self):
        """打开下载目录并选中文件"""
        if self.task.filename and os.path.exists(self.task.filename):
            if sys.platform == "win32":
                os.startfile(os.path.dirname(self.task.filename))
            else:
                subprocess.run(["open", "-R", self.task.filename])
        elif os.path.exists(self.task.download_path):
            if sys.platform == "win32":
                os.startfile(self.task.download_path)
            else:
                subprocess.run(["open", self.task.download_path])

    def show_error(self):
        """弹出详细错误信息"""
        if self.task.error:
            messagebox.showerror("下载错误详情", self.task.error)

    def delete(self):
        """删除下载任务"""
        self.task.stop()
        self.remove_callback(self)
        
        # 安全地访问主窗口的状态栏更新信息
        try:
            # 这里的 master.master 通常是 App 实例
            # 但为了鲁棒性，我们使用更加直接的查找方式或回溯
            curr = self.master
            while curr and not hasattr(curr, 'status_bar'):
                curr = curr.master
            if curr:
                curr.status_bar.configure(text=f"状态: 已移除任务 {self.task.title[:15]}...")
        except:
            pass

    def update_ui(self):
        """循环更新 UI 状态"""
        # 更新标题（如果太长则截断）
        display_title = self.task.title
        if len(display_title) > 35:
            display_title = display_title[:32] + "..."
        self.title_label.configure(text=display_title)
        
        self.status_label.configure(text=self.task.status)
        self.progress_bar.set(self.task.progress / 100)
        self.stats_label.configure(text=f"速度: {self.task.speed} | 剩余: {self.task.eta}")
        
        # 根据状态改变文字颜色和按钮功能
        if self.task.status == "下载完成":
            self.status_label.configure(text_color="#28A745")
            self.start_btn.configure(text="打开目录", state="normal", fg_color="#28A745", hover_color="#218838", command=self.open_folder)
            self.stop_btn.configure(state="disabled")
        elif self.task.status == "发生错误":
            self.status_label.configure(text_color="#DC3545", text="发生错误 (点击查看)")
            self.start_btn.configure(text="查看错误", state="normal", fg_color="#DC3545", hover_color="#C82333", command=self.show_error)
            self.stop_btn.configure(text="重试", state="normal", command=self.start)
        elif self.task.status == "正在下载":
            self.start_btn.configure(text="下载中", state="disabled")
            self.stop_btn.configure(text="停止", state="normal", command=self.stop)
        elif self.task.status == "已停止":
            self.start_btn.configure(text="继续", state="normal", command=self.start)
            self.stop_btn.configure(text="停止", state="disabled")
        
        # 只要任务还没落入“终态”，就每 0.5 秒更新一次界面
        # “等待中”也必须包含在轮询中，直到它真正开始下载
        terminal_statuses = ["下载完成", "发生错误", "已停止"]
        if self.task.status not in terminal_statuses:
            self.after(500, self.update_ui)

class App(ctk.CTk):
    """主程序窗口类"""
    def __init__(self):
        super().__init__()

        self.config = ConfigManager()
        self.engine = DownloaderEngine()
        self.item_frames = []

        # 窗口基本设置
        self.title("KKyt-dlp")
        self.geometry("900x750")
        
        # 针对不同操作系统的持久化路径
        if sys.platform == "win32":
            self.app_support_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "KKyt-dlp")
        else:
            self.app_support_dir = os.path.expanduser("~/Library/Application Support/KKyt-dlp")
        self.manual_cookies_path = os.path.join(self.app_support_dir, "cookies.txt")
        
        # 1. 确保核心二进制文件已就绪 (重要：防止由于路径问题导致的更新失败)
        self.engine.ensure_binaries()

        # 加载图标
        self.logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        try:
            # 关键：设置更高的尺寸并确保透明处理
            raw_img = Image.open(self.logo_path).convert("RGBA")
            self.logo_image = ctk.CTkImage(light_image=raw_img,
                                         dark_image=raw_img,
                                         size=(48, 48))
        except:
            self.logo_image = None
            
        # 2. 设置程序的运行时图标 (用于任务栏、Dock 和对话框)
        if self.logo_image:
            try:
                if sys.platform == "win32":
                    # Windows 专用图标设置
                    self.icon_path_ico = os.path.join(os.path.dirname(__file__), "logo.ico")
                    if os.path.exists(self.icon_path_ico):
                        # 延迟一点设置确保窗口句柄已完全准备好
                        self.after(200, lambda: self.iconbitmap(self.icon_path_ico))
                else:
                    # macOS / Linux
                    from tkinter import PhotoImage
                    self.icon_photo = PhotoImage(file=self.logo_path)
                    self.wm_iconphoto(True, self.icon_photo)
            except:
                pass

        # 主网格布局
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # 任务列表占满剩余空间

        # ---------------- 1. 品牌 Header ----------------
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        
        if self.logo_image:
            # 彻底去除 label 的边框和背景干扰，确保完全融合
            self.logo_label = ctk.CTkLabel(self.header_frame, image=self.logo_image, text="", 
                                           fg_color="transparent", bg_color="transparent",
                                           width=48, height=48, corner_radius=0)
            self.logo_label.pack(side="left", padx=(0, 10))
            
        self.title_label = ctk.CTkLabel(self.header_frame, text="KKyt-dlp Video Downloader", font=("Microsoft YaHei", 20, "bold"))
        self.title_label.pack(side="left")

        self.settings_btn = ctk.CTkButton(self.header_frame, text="⚙️ 设置", width=80, height=32, 
                                          fg_color="transparent", text_color="#333", border_width=1,
                                          command=self.open_settings)
        self.settings_btn.pack(side="right")

        # ---------------- 2. 顶部综合操作区 ----------------
        self.top_frame = ctk.CTkFrame(self, corner_radius=12)
        self.top_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
        self.top_frame.grid_columnconfigure(0, weight=1)

        # 第 1 行：URL 输入
        self.input_row = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.input_row.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(15, 10))
        self.input_row.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(self.input_row, placeholder_text="在此粘贴视频链接 (YouTube, Bilibili...)", height=45)
        self.url_entry.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="ew")

        self.add_btn = ctk.CTkButton(self.input_row, text="添加任务", width=120, height=45, 
                                     font=("Microsoft YaHei", 14, "bold"), command=self.add_to_queue)
        self.add_btn.grid(row=0, column=1, padx=(5, 10), pady=5)

        # 第 2 行：选项配置 (Cookie & 画质 & 格式) - 平均对齐
        self.option_row = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.option_row.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.option_row.grid_columnconfigure((0, 1, 2), weight=1)

        # 列 0: Cookie
        self.cookie_frame = ctk.CTkFrame(self.option_row, fg_color="transparent")
        self.cookie_frame.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.cookie_frame, text="Cookie 获取:", font=("Microsoft YaHei", 12)).pack(side="left", padx=2)
        self.cookie_var = ctk.StringVar(value="不使用")
        self.cookie_menu = ctk.CTkOptionMenu(self.cookie_frame, values=["不使用", "Chrome", "Edge", "Safari", "Firefox"], 
                                             variable=self.cookie_var, width=100)
        self.cookie_menu.pack(side="left", padx=2)

        # 列 1: 画质
        self.quality_frame = ctk.CTkFrame(self.option_row, fg_color="transparent")
        self.quality_frame.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(self.quality_frame, text="画质选择:", font=("Microsoft YaHei", 12)).pack(side="left", padx=2)
        self.quality_var = ctk.StringVar(value="最佳画质")
        self.quality_menu = ctk.CTkOptionMenu(self.quality_frame, values=["最佳画质", "1080p", "720p", "仅音频"], 
                                              variable=self.quality_var, width=100)
        self.quality_menu.pack(side="left", padx=2)

        # 列 2: 格式
        self.format_frame = ctk.CTkFrame(self.option_row, fg_color="transparent")
        self.format_frame.grid(row=0, column=2, sticky="nsew")
        ctk.CTkLabel(self.format_frame, text="保存格式:", font=("Microsoft YaHei", 12)).pack(side="left", padx=2)
        self.format_var = ctk.StringVar(value="MP4")
        self.format_menu = ctk.CTkOptionMenu(self.format_frame, values=["MP4", "WebM", "MKV", "MOV"], 
                                             variable=self.format_var, width=100)
        self.format_menu.pack(side="left", padx=2)

        # 第 3 行：专门的教学提示
        self.tip_label = ctk.CTkLabel(self.top_frame, 
                                      text="💡 提示: 仅在下载会员或年龄限制视频时选择浏览器，普通视频请选“不使用”以提高成功率。", 
                                      font=("Microsoft YaHei", 11), text_color="#777777")
        self.tip_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=25, pady=(2, 12))

        # ---------------- 3. 核心任务列表 (占满中部) ----------------
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="下载队列", label_font=("Microsoft YaHei", 14, "bold"))
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # ---------------- 4. 底部状态栏 ----------------
        self.bottom_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.bottom_frame.grid(row=3, column=0, sticky="ew")
        
        self.status_bar = ctk.CTkLabel(self.bottom_frame, text="状态: 准备就绪", font=("Microsoft YaHei", 12))
        self.status_bar.pack(side="left", padx=20)

        # 生命周期管理
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def add_to_queue(self):
        """解析输入并添加到界面"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入有效的视频地址后再点击添加。")
            return
        
        quality_map = {"最佳画质": "Best", "1080p": "1080p", "720p": "720p", "仅音频": "Audio Only"}
        cookie_map = {"不使用": "None", "Chrome": "Chrome", "Edge": "Edge", "Safari": "Safari", "Firefox": "Firefox"}
        format_map = {"MP4": "mp4", "WebM": "webm", "MKV": "mkv", "MOV": "mov"}
        
        quality = quality_map.get(self.quality_var.get(), "Best")
        cookies = cookie_map.get(self.cookie_var.get(), "None")
        video_format = format_map.get(self.format_var.get(), "mp4")
        
        # 使用配置项中的下载路径
        download_path = self.config.get("download_path")
        
        task = self.engine.add_task(url, quality, cookies, download_path, video_format)
        item = DownloadItem(self.scroll_frame, task, self.remove_item)
        item.grid(row=len(self.item_frames), column=0, padx=10, pady=8, sticky="ew")
        self.item_frames.append(item)
        
        self.url_entry.delete(0, 'end')
        self.status_bar.configure(text=f"状态: 已添加并自动开始下载")
        
        # 自动开始下载
        item.start()

    def open_settings(self):
        """打开设置窗口"""
        settings_win = ctk.CTkToplevel(self)
        settings_win.title("设置 / 关于")
        settings_win.geometry("500x620")
        settings_win.attributes("-topmost", True)
        
        # 强制设置子窗口图标
        if sys.platform == "win32" and hasattr(self, 'icon_path_ico'):
            settings_win.after(200, lambda: settings_win.iconbitmap(self.icon_path_ico))
            
        settings_win.grid_columnconfigure(0, weight=1)
        
        # 记录当前手动 Cookie 状态
        def get_cookie_status():
            if os.path.exists(self.manual_cookies_path):
                size = os.path.getsize(self.manual_cookies_path) / 1024
                return f"手动 Cookie: 已加载 ({size:.1f} KB)"
            return "手动 Cookie: 未导入 (推荐 YouTube 报错时使用)"

        self.cookie_status_var = ctk.StringVar(value=get_cookie_status())
        
        # 1. 关于部分
        ctk.CTkLabel(settings_win, text="关于 KKyt-dlp", font=("Microsoft YaHei", 16, "bold")).pack(pady=(20, 5))
        about_text = "KKyt-dlp v1.0 | 强效视频下载利器\n\n本程序由 AI 驱动开发，基于优秀的开源项目\nyt-dlp 与 FFmpeg 构建。致力于为您提供\n极简且强大的视频下载体验。"
        ctk.CTkLabel(settings_win, text=about_text, font=("Microsoft YaHei", 12), text_color="#666666").pack(pady=5)
        
        # 分隔线
        ctk.CTkFrame(settings_win, height=1, fg_color="#E0E0E0").pack(fill="x", padx=40, pady=15)

        # 2. 这里的配置
        ctk.CTkLabel(settings_win, text="默认下载保存路径", font=("Microsoft YaHei", 14, "bold")).pack(pady=(5, 10))
        
        path_frame = ctk.CTkFrame(settings_win, fg_color="transparent")
        path_frame.pack(fill="x", padx=20)
        
        path_var = ctk.StringVar(value=self.config.get("download_path"))
        path_entry = ctk.CTkEntry(path_frame, textvariable=path_var, width=300)
        path_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

        def browse_path():
            new_path = ctk.filedialog.askdirectory()
            if new_path:
                path_var.set(new_path)

        ctk.CTkButton(path_frame, text="浏览", width=80, command=browse_path).pack(side="right")

        def save_settings():
            self.config.set("download_path", path_var.get())
            self.status_bar.configure(text="状态: 设置已保存")
            settings_win.destroy()

        ctk.CTkButton(settings_win, text="保存设置", width=120, height=35, fg_color="#28A745", 
                      command=save_settings).pack(pady=10)

        # ---------------- 3. 手动 Cookie 管理 (解决 YouTube 认证问题) ----------------
        ctk.CTkLabel(settings_win, text="手动 Cookie 管理 (解决 YouTube 受限问题)", font=("Microsoft YaHei", 12, "bold")).pack(pady=(10, 5))
        
        cookie_frame = ctk.CTkFrame(settings_win, fg_color="transparent")
        cookie_frame.pack(fill="x", padx=20)
        
        self.cookie_label = ctk.CTkLabel(cookie_frame, textvariable=self.cookie_status_var, font=("Microsoft YaHei", 11), text_color="#666666")
        self.cookie_label.pack(side="left", padx=10)

        def import_cookies():
            file_path = ctk.filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
            if file_path:
                try:
                    os.makedirs(self.app_support_dir, exist_ok=True)
                    import shutil
                    shutil.copy2(file_path, self.manual_cookies_path)
                    self.cookie_status_var.set(get_cookie_status())
                    messagebox.showinfo("导入成功", "cookies.txt 已成功导入！\n下载时程序将自动优先使用该文件。")
                except Exception as e:
                    messagebox.showerror("导入失败", f"无法保存文件: {e}")

        def clear_cookies():
            if os.path.exists(self.manual_cookies_path):
                try:
                    os.remove(self.manual_cookies_path)
                    self.cookie_status_var.set(get_cookie_status())
                    messagebox.showinfo("清除成功", "已移除手动导入的 Cookie 文件。")
                except Exception as e:
                    messagebox.showerror("清除失败", f"无法删除文件: {e}")

        ctk.CTkButton(cookie_frame, text="导入 cookies.txt", width=100, command=import_cookies).pack(side="right", padx=5)
        ctk.CTkButton(cookie_frame, text="清除", width=60, fg_color="#6C757D", command=clear_cookies).pack(side="right", padx=5)

        # 分隔线
        ctk.CTkFrame(settings_win, height=1, fg_color="#E0E0E0").pack(fill="x", padx=40, pady=10)

        # 核心引擎管理
        ctk.CTkLabel(settings_win, text="核心引擎管理", font=("Microsoft YaHei", 12, "bold")).pack(pady=(5, 5))
        
        # 显示当前核心版本 (改为点击触发，避免进入设置卡顿)
        self.ver_label = ctk.CTkLabel(settings_win, text="核心版本: 未查询", font=("Microsoft YaHei", 11), text_color="#666666")
        self.ver_label.pack(pady=2)
        
        btn_frame = ctk.CTkFrame(settings_win, fg_color="transparent")
        btn_frame.pack(pady=5)

        self.check_ver_btn = ctk.CTkButton(btn_frame, text="查询当前版本", 
                                                width=120, height=30, 
                                                fg_color="#F8F9FA", text_color="#333", border_width=1,
                                                command=self.do_check_version)
        self.check_ver_btn.pack(side="left", padx=5)

        self.update_btn_settings = ctk.CTkButton(btn_frame, text="检查并更新核心插件", 
                                                width=120, height=30, 
                                                fg_color="#6C757D", hover_color="#5A6268", 
                                                command=self.update_core)
        self.update_btn_settings.pack(side="left", padx=5)

    def remove_item(self, item_frame):
        """从队列中移除任务及其 UI 卡片"""
        item_frame.grid_forget()
        if item_frame in self.item_frames:
            self.item_frames.remove(item_frame)
            self.engine.tasks.remove(item_frame.task)

    def do_check_version(self):
        """异步/手动查询核心版本，防止界面卡死"""
        self.ver_label.configure(text="核心版本: 正在查询...")
        self.update_idletasks()
        v = self.engine.get_version()
        self.ver_label.configure(text=f"核心版本: {v}")

    def update_core(self):
        """更新内置 yt-dlp 模块"""
        self.status_bar.configure(text="状态: 正在尝试更新核心组件，请稍候...")
        if hasattr(self, 'update_btn_settings'):
            self.update_btn_settings.configure(state="disabled")
        def do_update():
            # 先记录当前版本
            try:
                old_ver = self.engine.get_version()
                success = self.engine.update_core()
                new_ver = self.engine.get_version()
                
                if success == "LATEST":
                    self.status_bar.configure(text=f"状态: 核心组件已是最新版本 ({new_ver})")
                    messagebox.showinfo("核心更新", f"您的核心组件已是最新版本 ({new_ver})，无需更新。")
                elif success:
                    if old_ver == new_ver:
                        self.status_bar.configure(text=f"状态: 核心组件已是最新版本 ({new_ver})")
                        messagebox.showinfo("核心更新", f"您的核心组件已是最新版本 ({new_ver})，无需更新。")
                    else:
                        self.status_bar.configure(text=f"状态: 核心组件已成功更新到 {new_ver}！")
                        if hasattr(self, 'ver_label'):
                            self.ver_label.configure(text=f"当前核心版本: {new_ver}")
                        messagebox.showinfo("核心更新", f"核心组件更新成功！\n原版本: {old_ver}\n现版本: {new_ver}")
                else:
                    err_detail = self.engine.last_error
                    self.status_bar.configure(text=f"状态: 更新失败: {err_detail[:30]}...")
                    messagebox.showerror("更新失败", f"无法连接到更新服务器或权限不足。\n\n技术详情:\n{err_detail}\n\n建议: 请检查网络，如有代理请尝试开启或关闭。")
            except Exception as e:
                messagebox.showerror("更新错误", f"更新过程中发生异常: {e}")
                
            if hasattr(self, 'update_btn_settings'):
                self.update_btn_settings.configure(state="normal")
            
        import threading
        threading.Thread(target=do_update, daemon=True).start()

    def on_closing(self):
        """安全关闭程序：先终结所有下载与合并进程"""
        self.status_bar.configure(text="状态: 正在清理后台进程...")
        for frame in self.item_frames:
            frame.task.stop()
        
        # 延迟片刻确保进程已被操作系统完全回收
        self.after(500, self.destroy)
        sys.exit(0)

if __name__ == "__main__":
    # Windows 任务栏图标修复
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("mycompany.kkyt-dlp.v1")
        except:
            pass
            
    app = App()
    app.mainloop()
