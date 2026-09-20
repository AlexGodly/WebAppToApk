@echo off
cd /d "%~dp0"
where py.exe >nul 2>&1 && (py web2apk.py & exit /b)
python web2apk.py
