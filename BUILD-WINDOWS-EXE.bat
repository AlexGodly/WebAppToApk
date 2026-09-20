@echo off
setlocal
cd /d "%~dp0"
title Build Web2APK Windows EXE

echo ============================================================
echo              Build Web2APK Windows EXE
echo ============================================================
echo.

where py.exe >nul 2>&1
if errorlevel 1 (
  where python.exe >nul 2>&1 || (
    echo ERROR: Python 3 is not installed or not in PATH.
    echo Install Python 3, then run this file again.
    pause
    exit /b 1
  )
  set "PY=python"
) else (
  set "PY=py"
)

echo Installing/updating build dependencies...
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: Could not install Python dependencies.
  pause
  exit /b 1
)

echo.
echo Building Web2APK.exe...
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name Web2APK web2apk.py
if errorlevel 1 (
  echo ERROR: EXE build failed.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo BUILD SUCCESSFUL
echo ============================================================
echo EXE:
echo %CD%\dist\Web2APK.exe
echo ============================================================
explorer.exe /select,"%CD%\dist\Web2APK.exe"
pause
