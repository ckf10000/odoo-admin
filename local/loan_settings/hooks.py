# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  admin
# FileName:     hooks.py
# Description:  TODO
# Author:       Administrator
# CreateDate:   2024/11/12
# Copyright ©2011-2024. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import logging
import threading
from odoo import sql_db
from datetime import datetime, timezone


def post_load():
    _logger = logging.getLogger(__name__)

    _logger.info("************** execute hook function: post_load  **************")

    dbname = getattr(threading.current_thread(), 'dbname', '?')
    _logger.info("Connect DBname ---> %s", dbname)
    cur = None
    try:
        # 获取数据库连接
        cur = sql_db.db_connect(dbname).cursor()
        # 执行 SQL 查询
        cur.execute("SELECT id, name FROM res_groups")
        results = cur.fetchall()
        res_groups_id = 0
        name = "催收员"
        if results and len(results) > 0:
            for result in results:
                if isinstance(result[1], dict):
                    if result[1].get("en_US") == name or result[1].get("zh_CN") == name:
                        res_groups_id = result[0]
                        break
        else:
            _logger.info("No Res Groups results found for query")
        employee_menu_id: int = 0
        # 执行 SQL 查询
        cur.execute("SELECT id, name, parent_id, parent_path FROM ir_ui_menu")
        results = cur.fetchall()
        if results and len(results) > 0:
            for result in results:
                if isinstance(result[1], dict):
                    if result[1].get("en_US") == "Employees":
                        if isinstance(result[3], str) and len(result[3].split("/")) == 2:
                            employee_menu_id = result[0]
                            break
        # 移除 ir_ui_menu_group_rel 关系表中 employee_menu_id 与 角色id 为 1 的数据关系
        cur.execute("DELETE FROM ir_ui_menu_group_rel WHERE menu_id=%s and gid=1", (employee_menu_id,))
        if res_groups_id > 0:
            cur.execute(f'SELECT * FROM "R_role" where res_groups_id=%s', (res_groups_id,))
            result = cur.fetchone()
            if result:
                _logger.warning("----催收员--- 角色已存在.")
            else:
                # 指定 UTC 时区
                ts = datetime.now(timezone.utc)
                insert_collection_sql_slice = [
                    "insert into ",
                    '"R_role" ',
                    "(res_groups_id,company_id,create_uid,write_uid,sequence,name," +
                    "access_limit,create_date,write_date,active) ",
                    "values ",
                    f"({res_groups_id},1,2,2,'00000','{name}','1','{ts}','{ts}','t')"
                ]
                cur.execute(''.join(insert_collection_sql_slice))
        cur.commit()
        cur.close()
    except Exception as e:
        _logger.error("Error occurred during post-load hook: %s", str(e))
        if cur:
            cur.close()
