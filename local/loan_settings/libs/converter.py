# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  admin
# FileName:     converter.py
# Description:  TODO
# Author:       Administrator
# CreateDate:   2024/11/06
# Copyright ©2011-2024. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""


class ModelKwargsConverter:

    @staticmethod
    def get_res_partner_kwargs(vals: dict) -> dict:
        kwargs = dict()
        if "name" in vals:
            kwargs['name'] = kwargs['complete_name'] = vals["name"]
        if "phone" in vals:
            kwargs['phone'] = vals["phone"]
        if "lang" in vals:
            kwargs['lang'] = vals["lang"]
        if "tz" in vals:
            kwargs['tz'] = vals["tz"]
        if "active" in vals:
            kwargs['active'] = vals["active"]
        return kwargs

    @staticmethod
    def get_res_company_kwargs(vals: dict) -> dict:
        kwargs = dict()
        if "name" in vals:
            kwargs['name'] = vals["name"]
        if "phone" in vals:
            kwargs['phone'] = vals["phone"]
        return kwargs

    @staticmethod
    def parse_many2many_args(*args) -> tuple:
        add_list = list()
        del_list = list()
        for arg in args:
            if arg[0] == 3:
                del_list.append(arg[1])
            elif arg[0] == 4:
                add_list.append(arg[1])
        return add_list, del_list
