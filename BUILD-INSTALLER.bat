@echo off
setlocal
cd /d "%~dp0"
title Build Web2APK Installer
if not exist "dist\Web2APK.exe" (
 call BUILD-WINDOWS-EXE.bat
 if errorlevel 1 exit /b 1
)
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC (
 echo ERROR: Inno Setup 6 is not installed.
 echo Install Inno Setup 6, then run this again.
 pause
 exit /b 1
)
"%ISCC%" "installer.iss"
if errorlevel 1 (echo INSTALLER BUILD FAILED&pause&exit /b 1)
echo SUCCESS: %CD%\installer\Web2APK-Setup-v1.0.1.exe
explorer.exe /select,"%CD%\installer\Web2APK-Setup-v1.0.1.exe"
pause
