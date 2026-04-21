import os
import json

class ConfigManager:
    """管理应用程序配置（如保存目录等）"""
    APP_NAME = "KKyt-dlp"
    
    def __init__(self):
        # 针对 macOS 的配置路径: ~/Library/Application Support/KKyt-dlp/
        self.config_dir = os.path.expanduser(f"~/Library/Application Support/{self.APP_NAME}")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.default_config = {
            "download_path": os.path.expanduser("~/Downloads"),
            "appearance_mode": "Light",
            "max_concurrent": 3,
            "language": "zh"
        }
        self.config = self.load_config()

    def load_config(self):
        """从 JSON 加载配置，若不存在则创建默认"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
            
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并默认配置，防止缺失字段
                    return {**self.default_config, **user_config}
            except:
                return self.default_config
        else:
            self.save_config(self.default_config)
            return self.default_config

    def save_config(self, config_data=None):
        """保存配置到文件"""
        if config_data:
            self.config = config_data
        
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get(self, key):
        """获取配置项"""
        return self.config.get(key, self.default_config.get(key))

    def set(self, key, value):
        """更新配置项并保存"""
        self.config[key] = value
        self.save_config()
