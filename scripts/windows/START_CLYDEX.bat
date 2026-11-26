@echo off
cd /d "%~dp0..\.."
where pythonw.exe >nul 2>nul
if errorlevel 1 (
    start "" pyw "%~dp0clydex_widget.pyw"
) else (
    start "" pythonw "%~dp0clydex_widget.pyw"
)
