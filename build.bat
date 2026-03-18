@echo off
echo Building FFmpeg PATH Installer...

REM Install dependencies
pip install -r requirements.txt

REM Build executable with PyInstaller
pyinstaller --onefile --windowed --icon=ffmpeg.ico --add-data "ffmpeg.ico;." --name="FFmpeg_to_PATH_Installer" ffmpeg_installer.py

echo Build complete! FFmpeg_PATH_Installer.exe created.
echo.
echo This installer will help users add FFmpeg to their PATH automatically.
echo Users just need to run the exe and follow the GUI instructions.
pause