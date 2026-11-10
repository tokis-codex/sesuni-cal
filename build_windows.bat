@echo off
setlocal
cd /d "%~dp0"
echo [1/3] Checking Python...
py -3 --version
if errorlevel 1 goto :python_fail
echo [2/3] Installing requirements...
py -3 -m pip install --upgrade PySide6 pyinstaller
if errorlevel 1 goto :fail
echo [3/3] Building Windows EXE...
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name Sesuni_Calculator --icon date_calculator.ico --add-data "date_calculator.ico;." --add-data "gmail_fallback.png;." --add-data "daum_fallback.png;." --add-data "naver_fallback.png;." --add-data "history_tab.png;." --add-data "calendar_tab.png;." date_calculator.py
if errorlevel 1 goto :fail
echo.
echo Build completed: dist\Sesuni_Calculator.exe
echo The window title is displayed in Korean.
pause
exit /b 0
:python_fail
echo Python 3 not found. Install Python 3.11-3.13 and enable py launcher.
pause
exit /b 1
:fail
echo Build failed. Check error messages above.
pause
exit /b 1
