@echo off
cd /d "%~dp0"
where pythonw.exe >nul 2>nul
if errorlevel 1 (
    start "" pyw "clydex_widget.pyw"
) else (
    start "" pythonw "clydex_widget.pyw"
)
