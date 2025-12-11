@echo off
chcp 65001 >nul
cd /d %~dp0
python check_and_import_missing_laws.py --repo-path "E:\Laws\Laws"
pause
