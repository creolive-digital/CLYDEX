@echo off
cd /d "%~dp0..\.."
python -m pip install -r deployment\windows\requirements.txt
pause
