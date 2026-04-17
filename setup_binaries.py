import os
import sys
import zipfile
import subprocess
from urllib.request import urlretrieve

def download_and_extract(url, target_name):
    temp_zip = f"{target_name}.zip"
    print(f"正在从 {url} 下载 {target_name}...")
    urlretrieve(url, temp_zip)
    
    print(f"正在解压 {temp_zip}...")
    with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
        zip_ref.extractall("bin")
    
    os.remove(temp_zip)
    
    # 设置可执行权限
    bin_path = os.path.join("bin", target_name)
    if os.path.exists(bin_path):
        os.chmod(bin_path, 0o755)
        print(f"成功安装并配置 {target_name}")
    else:
        # 某些 zip 可能会包含子文件夹
        print(f"警告：在解压根目录未找到 {target_name}。正在搜索子目录...")
        for root, dirs, files in os.walk("bin"):
            for file in files:
                if file == target_name:
                    found_path = os.path.join(root, file)
                    os.chmod(found_path, 0o755)
                    print(f"在 {found_path} 找到并配置了 {file}")

def main():
    if not os.path.exists("bin"):
        os.makedirs("bin")
    
    # Evermeet.cx 提供的 macOS 静态二进制文件，以及 GitHub 上的 yt-dlp
    urls = {
        "ffmpeg": "https://evermeet.cx/ffmpeg/get/zip",
        "ffprobe": "https://evermeet.cx/ffmpeg/get/ffprobe/zip",
        "yt-dlp": "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos"
    }
    
    for name, url in urls.items():
        try:
            if url.endswith("/zip"):
                download_and_extract(url, name)
            else:
                # 非 ZIP 文件（如 yt-dlp_macos）
                print(f"正在从 {url} 下载 {name}...")
                target_path = os.path.join("bin", name)
                urlretrieve(url, target_path)
                os.chmod(target_path, 0o755)
                print(f"成功安装并配置 {name}")
        except Exception as e:
            print(f"下载 {name} 失败: {e}")
            print(f"请手动下载 macOS 版的 {name} 并放入 'bin' 文件夹中。")

if __name__ == "__main__":
    main()
