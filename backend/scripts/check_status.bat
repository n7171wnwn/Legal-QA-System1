@echo off
chcp 65001 >nul
cd /d %~dp0
python show_status.py
pause
