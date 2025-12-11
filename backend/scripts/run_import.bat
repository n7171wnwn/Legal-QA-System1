@echo off
chcp 65001
cd /d %~dp0
echo ========================================
echo 开始导入所有未导入的法律法条
echo ========================================
python import_laws_data.py --repo-path "E:\Laws\Laws"
echo.
echo ========================================
echo 导入完成！按任意键退出...
pause >nul
