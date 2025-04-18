# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  admin
# FileName:     repository.py
# Description:  TODO
# Author:       Administrator
# CreateDate:   2024/11/07
# Copyright ©2011-2024. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from odoo import models


class ModelRepository(object):

    @classmethod
    def get_administrator_ids(cls, model: models.Model) -> list:
        admin_ids = list()
        model.env.cr.execute("select * from res_groups")
        # 获取查询结果
        res_groups_ids = model.env.cr.fetchall()
        for res_groups_id in res_groups_ids:
            if res_groups_id[1].get("en_US") == "Administrator":
                admin_ids.append(res_groups_id[0])
        return admin_ids
