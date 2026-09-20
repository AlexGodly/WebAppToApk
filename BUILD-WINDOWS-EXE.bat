@echo off
setlocal
cd /d "%~dp0"
title Build Web2APK
where py.exe >nul 2>&1 && (set "PY=py") || (set "PY=python")
%PY% -m pip install -r requirements.txt
if errorlevel 1 goto fail
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name Web2APK --icon "web2apk.ico" --version-file "version_info.txt" web2apk.py
if errorlevel 1 goto fail
echo SUCCESS: %CD%\dist\Web2APK.exe
explorer.exe /select,"%CD%\dist\Web2APK.exe"
pause
exit /b 0
:fail
echo BUILD FAILED
pause
exit /b 1
