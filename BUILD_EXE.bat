@echo off
cd /d "%~dp0"
echo Installing build dependencies...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
echo Building AKYR Client...
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "AKYR Client" --collect-all minecraft_launcher_lib main.py
if errorlevel 1 (
  echo Build failed. Read the error above.
  pause
  exit /b 1
)
echo.
echo Finished: dist\AKYR Client.exe
pause
