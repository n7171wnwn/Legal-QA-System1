@echo off
chcp 65001 >nul
echo ========================================
echo 案例数据导入脚本
echo ========================================
echo.

cd /d %~dp0

python import_cases_data.py --repo-path E:\Laws\Laws --password hjj060618

pause

