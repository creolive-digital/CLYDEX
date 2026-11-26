@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0..\.."
title CLYDEX — Build Installer

echo ============================================================
echo  CLYDEX Installer Build Script
echo ============================================================
echo.

:: ── 1. Check Python ──────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ and add it to PATH.
    pause & exit /b 1
)
echo [OK] Python found.

:: ── 2. Install / upgrade build tools ─────────────────────────
echo.
echo Installing PyInstaller ^>= 6.0 and hooks...
python -m pip install --upgrade "pyinstaller>=6.0" pyinstaller-hooks-contrib
if errorlevel 1 ( echo ERROR: pip install failed. & pause & exit /b 1 )
echo [OK] PyInstaller ready.

:: ── 3. Build the widget exe ───────────────────────────────────
echo.
echo Building clydex_widget.exe ...
python -m PyInstaller --clean --noconfirm --distpath deployment\windows\artifacts\dist --workpath deployment\windows\artifacts\build installer\pyinstaller\clydex_widget.spec
if errorlevel 1 ( echo ERROR: Widget build failed. & pause & exit /b 1 )
echo [OK] Widget built  →  deployment\windows\artifacts\dist\clydex_widget\

:: ── 4. Build the voice agent exe ─────────────────────────────
echo.
echo Building clydex_voice_agent.exe  (this takes a few minutes) ...
python -m PyInstaller --clean --noconfirm --distpath deployment\windows\artifacts\dist --workpath deployment\windows\artifacts\build installer\pyinstaller\clydex_voice_agent.spec
if errorlevel 1 ( echo ERROR: Voice agent build failed. & pause & exit /b 1 )
echo [OK] Voice agent built  →  deployment\windows\artifacts\dist\clydex_voice_agent\

:: ── 5. Run Inno Setup ─────────────────────────────────────────
echo.
set ISCC=
for %%P in (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
    "C:\Program Files (x86)\Inno Setup 6\Compil32.exe"
) do (
    if exist %%P ( set "ISCC=%%~P" & goto :found_iscc )
)

echo WARNING: Inno Setup 6 not found.
echo   Download from https://jrsoftware.org/isinfo.php
echo   Then re-run this script, or open installer\windows\installer.iss manually in Inno Setup.
echo.
echo The two EXE builds are ready under deployment\windows\artifacts\dist\  — you can zip and ship them
echo without the installer if needed.
pause & exit /b 0

:found_iscc
echo [OK] Inno Setup found at: %ISCC%
echo.
echo Compiling installer...
if not exist deployment\windows\artifacts\installer mkdir deployment\windows\artifacts\installer
"%ISCC%" installer\windows\installer.iss
if errorlevel 1 ( echo ERROR: Inno Setup compilation failed. & pause & exit /b 1 )

echo.
echo ============================================================
echo  SUCCESS!  Installer ready:
echo    deployment\windows\artifacts\installer\CLYDEX_Setup.exe
echo ============================================================
echo.
pause
