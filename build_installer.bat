@echo off
setlocal EnableDelayedExpansion
title CLYDEX — Build Installer

echo ============================================================
echo  CLYDEX Installer Build Script
echo ============================================================
echo.

:: ── 1. Check Python ──────────────────────────────────────────
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ and add it to PATH.
    pause & exit /b 1
)
echo [OK] Python found.

:: ── 2. Install / upgrade build tools ─────────────────────────
echo.
echo Installing PyInstaller ^>= 6.0 and hooks...
py -m pip install --upgrade "pyinstaller>=6.0" pyinstaller-hooks-contrib
if errorlevel 1 ( echo ERROR: pip install failed. & pause & exit /b 1 )
echo [OK] PyInstaller ready.

:: ── 3. Build the widget exe ───────────────────────────────────
echo.
echo Building clydex_widget.exe ...
py -m PyInstaller --clean --noconfirm clydex_widget.spec
if errorlevel 1 ( echo ERROR: Widget build failed. & pause & exit /b 1 )
echo [OK] Widget built  →  dist\clydex_widget\

:: ── 4. Build the voice agent exe ─────────────────────────────
echo.
echo Building clydex_voice_agent.exe  (this takes a few minutes) ...
py -m PyInstaller --clean --noconfirm clydex_voice_agent.spec
if errorlevel 1 ( echo ERROR: Voice agent build failed. & pause & exit /b 1 )
echo [OK] Voice agent built  →  dist\clydex_voice_agent\

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
echo   Then re-run this script, or open installer.iss manually in Inno Setup.
echo.
echo The two EXE builds are ready under dist\  — you can zip and ship them
echo without the installer if needed.
pause & exit /b 0

:found_iscc
echo [OK] Inno Setup found at: %ISCC%
echo.
echo Compiling installer...
if not exist installer_out mkdir installer_out
"%ISCC%" installer.iss
if errorlevel 1 ( echo ERROR: Inno Setup compilation failed. & pause & exit /b 1 )

echo.
echo ============================================================
echo  SUCCESS!  Installer ready:
echo    installer_out\CLYDEX_Setup.exe
echo ============================================================
echo.
pause
