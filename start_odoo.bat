@echo off
chcp 65001 >nul
set TZ=Asia/Shanghai

title Odoo-Server

D:\workspace\Python\python_env\odoo-17\Scripts\python.exe ^
    D:\workspace\Python\odoo\odoo-bin ^
    --dev=all ^
    -c D:\workspace\Python\odoo-admin\odoo.windows.conf