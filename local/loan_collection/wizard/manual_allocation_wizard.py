# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import date


class ManualAllocationWizard(models.TransientModel):
    _name = 'manual.allocation.wizard'
    _table = 'C_manual_allocation_wizard'
    _description = '手动分单向导'

    selected_ids = fields.Integer(string=_('The Selected Order Quantity'))
    collection_stage = fields.Char(string=_('Collection Stage'))
    collector_id = fields.Many2one('res.users', string=_('Allocation Target'))  # 催收员

    def action_confirm(self):
        """
        确认按钮
        """
        lang = self.env.user.lang
        if not self.collector_id:
            msg = '没有可选对象，请调整"分单管理"配置!' if lang == "zh_CN" else \
                "There are no selectable objects, please adjust the 'Order Allocation Management' configuration!"
            raise ValidationError(msg)
        else:
            order_ids = self.env['collection.order'].browse(self._context.get('active_ids'))
            # 催收员必须是当前催收阶段，进件已开启
            points_id = self.env['collection.points'].sudo().search([
                ('user_id', '=', self.collector_id.id),
                ('collection_stage', '=', self.collection_stage),
                ('is_input', '=', True)
            ], limit=1)
            today_allocated_qty = self.env['collector.link.order.record'].sudo().search_count([('collector_id', '=', points_id.user_id.id), ('allot_date', '=', date.today())])
            # order_ids： 催收订单
            # points_id.loan_product_ids.ids: 催收员关联的产品id
            can_allocated_ids = order_ids.filtered(lambda x: x.loan_order_id.product_id.id in points_id.loan_product_ids.ids)
            can_count = len(can_allocated_ids)
            not_included_product = self.selected_ids - can_count
            order_status_id = self.env['collection.order.status'].sudo().search([('code', '=', '2')]).id
            # 如果选择的订单 可以完全分配则执行并返回执行成功
            if points_id.max_daily_intake > today_allocated_qty + can_count:
                if can_allocated_ids:
                    for can_allocated_id in can_allocated_ids:
                        self.env.cr.execute(
                            f'update "C_order" set order_status_id={order_status_id},collector_id=' +
                            f'{points_id.user_id.id} where id={can_allocated_id.id}'
                        )
                        self.env['collector.link.order.record'].sudo().create(
                            {
                                'company_id': can_allocated_id.company_id.id,
                                'collector_id': points_id.user_id.id,
                                'collection_order_id': can_allocated_id.id,
                                'allot_date': date.today()
                            }
                        )
                if self.selected_ids == can_count:
                    message = '分单成功' if lang == "zh_CN" else "Assignation successful!"
                else:
                    message = f'分单成功数量：{can_count}, \n分单失败数量：{not_included_product} \n(订单产品不属于该催收员"进件产品"范围)' if lang == "zh_CN" else f'Number of successful assignation orders: {can_count}, \nNumber of failed assignation orders：{not_included_product} \n(The ordered product is not within the scope of the "Incoming Product Type" of the collector)'
            elif today_allocated_qty < points_id.max_daily_intake < today_allocated_qty + can_count:
                allocated_order_ids = can_allocated_ids[:points_id.max_daily_intake - today_allocated_qty]
                if allocated_order_ids:
                    for allocated_order_id in allocated_order_ids:
                        self.env.cr.execute(
                            f'update "C_order" set order_status_id={order_status_id},collector_id=' +
                            f'{points_id.user_id.id} where id={allocated_order_id.id}'
                        )
                        self.env['collector.link.order.record'].sudo().create(
                            {
                                'company_id': allocated_order_id.company_id.id,
                                'collector_id': points_id.user_id.id,
                                'collection_order_id': allocated_order_id.id,
                                'allot_date': date.today()
                            }
                        )
                failed_total = can_count - (points_id.max_daily_intake - today_allocated_qty)
                message = f"分单成功数量：{len(allocated_order_ids)}, \n分单失败数量：{failed_total} \n(已达到该催收员今日进件上限)" if lang == "zh_CN" else f"Number of successful assignation orders：{len(allocated_order_ids)}, \nNumber of failed assignation orders：{failed_total} \n(The collector has reached the daily case intake limit.)"
                if not_included_product > 0:
                    sub_message = f', \n分单失败数量：{not_included_product} \n(订单产品不属于该催收员"进件产品"范围)' if lang == "zh_CN" else f', \nNumber of failed assignation orders：{not_included_product} \n(The ordered product is not within the scope of the "Incoming Product Type" of the collector)'
                    message = message + sub_message
            else:
                message = f"分单成功数量：0, \n分单失败数量：{self.selected_ids} \n(已达到该催收员今日进件上限)" if lang == "zh_CN" else f"Number of successful assignation orders：0, \nNumber of failed assignation orders：{self.selected_ids} \n(The collector has reached the daily case intake limit.)"
                if not_included_product > 0:
                    sub_message = f', \n分单失败数量：{not_included_product} \n(订单产品不属于该催收员"进件产品"范围)' if lang == "zh_CN" else f', \nNumber of failed assignation orders：{not_included_product} \n(The ordered product is not within the scope of the "Incoming Product Type" of the collector)'
                    message = message + sub_message
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '提示' if lang == "zh_CN" else "Prompt",
                    'message': message,
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }



class ManualAllocationTitleWizard(models.TransientModel):
    _name = 'manual.allocation.title.wizard'
    _description = '手动分单提示'