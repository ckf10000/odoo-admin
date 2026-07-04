@echo off
chcp 65001 >nul
setlocal

:: ============ 配置区域 ============

:: Python 解释器路径
set PYTHON=D:\workspace\Python\python_env\odoo-17\Scripts\python.exe

:: Odoo 入口文件
set ODOO_BIN=D:\workspace\Python\odoo\odoo-bin

:: 配置文件路径
set ODOO_CONF=D:\workspace\Python\odoo-admin\odoo.windows.conf

:: 数据库名称
set DB_NAME=mydb

:: 初始化安装的模块（多个用逗号分隔）
set MODULES=base

:: 时区设置（解决日志 UTC+0 问题）
set TZ=Asia/Shanghai

:: ============ 配置区域结束 ============

echo ============================================
echo   Odoo 数据库初始化脚本
echo ============================================
echo.
echo Python:     %PYTHON%
echo Odoo:       %ODOO_BIN%
echo 配置文件:   %ODOO_CONF%
echo 安装模块:   %MODULES%
echo.

:: 检查 Python 是否存在
if not exist "%PYTHON%" (
    echo [错误] 找不到 Python: %PYTHON%
    pause
    exit /b 1
)

:: 检查 odoo-bin 是否存在
if not exist "%ODOO_BIN%" (
    echo [错误] 找不到 odoo-bin: %ODOO_BIN%
    pause
    exit /b 1
)

:: 检查配置文件是否存在
if not exist "%ODOO_CONF%" (
    echo [错误] 找不到配置文件: %ODOO_CONF%
    pause
    exit /b 1
)

:: 询问是否继续
set /p CONFIRM=确认开始初始化？(Y/N):
if /i not "%CONFIRM%"=="Y" (
    echo 已取消操作。
    pause
    exit /b 0
)


:: 执行初始化
"%PYTHON%" "%ODOO_BIN%" -c "%ODOO_CONF%" -i %MODULES% --stop-after-init --dev=all

:: 检查执行结果
if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo   初始化完成！
    echo ============================================
) else (
    echo.
    echo ============================================
    echo   初始化失败！请检查上方错误信息
    echo ============================================
)

echo.
pause