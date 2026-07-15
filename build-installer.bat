@echo off
REM LocWarp, one-shot build: backend exe + electron installer.
REM Prereqs (install once):
REM   - Python 3.13  + pip install -r backend/requirements.txt pyinstaller
REM   - Node.js 18+  + cd frontend && npm install && npm install -D electron-builder

setlocal enabledelayedexpansion
cd /d "%~dp0"
set ROOT=%cd%

set PYTHON313=
if exist "%ROOT%\venv\Scripts\python.exe" set "PYTHON313=%ROOT%\venv\Scripts\python.exe"
if not defined PYTHON313 for /f "delims=" %%I in ('py -3.13 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON313=%%I"
if not defined PYTHON313 (
    echo Python 3.13 is required but was not found.
    echo Install Python 3.13, then run this script again.
    exit /b 1
)

"%PYTHON313%" -c "import ssl,sys; assert sys.version_info[:2] == (3,13), sys.version; assert callable(getattr(ssl.SSLContext,'set_psk_client_callback',None)), 'TLS-PSK unavailable'"
if errorlevel 1 (echo Python 3.13 TLS-PSK validation failed & exit /b 1)

echo.
echo ============================================================
echo  [1/3] Build backend (Python 3.13) with PyInstaller
echo ============================================================
cd /d "%ROOT%\backend"
"%PYTHON313%" -m PyInstaller locwarp-backend.spec --noconfirm --distpath "%ROOT%\dist-py" --workpath "%ROOT%\build-py\backend"
if errorlevel 1 (echo backend build failed & exit /b 1)

echo.
echo ============================================================
echo  [2/3] Build frontend (Vite)
echo ============================================================
cd /d "%ROOT%\frontend"
call npm run build
if errorlevel 1 (echo frontend build failed & exit /b 1)

echo.
echo ============================================================
echo  [3/3] Package Electron installer (electron-builder)
echo ============================================================
call npx electron-builder --win nsis
if errorlevel 1 (echo installer build failed & exit /b 1)

echo.
echo ============================================================
echo  DONE, installer is in frontend\release\
echo ============================================================
dir /b "%ROOT%\frontend\release\*.exe"
endlocal
