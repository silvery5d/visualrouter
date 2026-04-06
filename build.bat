@echo off
echo Installing dependencies...
pip install PySide6 pyinstaller

echo Building executable...
pyinstaller build_windows.spec --clean

echo Done! Output in dist/ folder
pause
