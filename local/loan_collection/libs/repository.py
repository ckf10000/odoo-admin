# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  admin
# FileName:     repository.py
# Description:  TODO
# Author:       Administrator
# CreateDate:   2024/11/29
# Copyright ©2011-2024. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from datetime import date
from c_base.biz.data.d_order_info import D_order_info
from c_base.biz.data.d_collector_info import D_collector_info
from c_base.data_provider.dp_def.dp_def_auto_assign import IDataProvider_auto_assign


class DataProvider_auto_assign(IDataProvider_auto_assign):

    def __init__(self, env):
        self.env = env

    # return: dict[order_id, D_order_info]
    def load_orders_to_assign(self) -> dict[int, D_order_info] | None:
        order_status_id = self.env["collection.order.status"].search(
            [("code", "=", "1")], limit=1
        )
        allot_order_ids = self.env["collection.order"].search(
            [("order_status_id", "=", order_status_id.id)]
        )
        return {allot_order_id.id: D_order_info(
            order_id=allot_order_id.id,
            product_id=allot_order_id.product_id.id,
            phase_code=str(allot_order_id.collection_stage_setting_id.id)
        ) for allot_order_id in allot_order_ids if allot_order_id.collection_stage_setting_id.id}

    # return: dict[collector_id, D_collector_info]
    def load_available_collectors(self) -> dict[int, D_collector_info] | None:
        result = dict()
        points_ids = self.env["collection.points"].search(
            [("is_input", "=", True), ("user_id.active", "=", True)]
        )
        for points_id in points_ids:
            today_allocated_count = self.env[
                "collector.link.order.record"
            ].sudo().search_count(
                [
                    ("collector_id", "=", points_id.user_id.id),
                    ("allot_date", "=", date.today()),
                ]
            )
            if points_id.max_daily_intake - today_allocated_count > 0:
                result[points_id.user_id.id] = D_collector_info(
                    collector_id=points_id.user_id.id,
                    status_code=1,
                    phase_code=str(points_id.collection_stage_id.id) if points_id.collection_stage_id.id else "",
                    daily_limit=points_id.max_daily_intake - today_allocated_count,
                    assignable_flag=True,
                    product_scope=points_id.loan_product_ids.ids,
                    whole_scope_flag=True if points_id.loan_product_ids_str in ("全部", "all") else False,
                    account_open_flag=True,
                    assigned_orders=list()
                )
        return result
