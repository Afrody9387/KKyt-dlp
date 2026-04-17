@echo off
echo ======================================================
echo   KKyt-dlp Windows One-Click Build Script
echo ======================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+.
    pause
    exit /b
)

:: 2. Install Dependencies
echo [1/3] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

:: 3. Prepare Binaries
if not exist "bin\yt-dlp.exe" (
    echo [WARNING] bin\yt-dlp.exe not found. Downloading...
    curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe -o bin\yt-dlp.exe
)
if not exist "bin\ffmpeg.exe" (
    echo [ERROR] bin\ffmpeg.exe not found. 
    echo Please put ffmpeg.exe into the 'bin' folder first.
    pause
    exit /b
)

:: 4. Build EXE
echo [2/3] Building with PyInstaller...
pyinstaller --noconfirm KKyt-dlp_Windows.spec

echo.
echo [3/3] Done! Your Windows App is in 'dist/KKyt-dlp'
echo ======================================================
pause
