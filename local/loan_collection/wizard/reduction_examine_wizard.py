# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime


class ReductionExamineWizard(models.TransientModel):
    _name = 'reduction.examine.wizard'
    _table = 'C_reduction_examine_wizard'
    _description = '金额减免流程向导'

    flow_type = fields.Selection([('batch', '批量审核'),
                                  ('audit', '通过'),
                                  ('fail', '拒绝')], string='金额减免流程')
    selected_ids = fields.Integer(string='已选择订单数量')
    total_annul_amount = fields.Float(string='合计申请减免金额', digits=(16, 2))
    display_info = fields.Char(string='提示信息')
    batch_flow_type = fields.Selection([('audit', '通过'),
                                        ('fail', '拒绝')], string='批量审核')
    remark = fields.Char(string='备注')

    # def _compute_display_info(self):
    #     if self.flow_type == 'batch':
    #         self.display_info = '已选择订单数量：%s，合计申请减免金额：%s' % (self.selected_ids, self.total_annul_amount)
    #     elif self.flow_type == 'audit':
    #         self.display_info = '申请减免金额：%s，是否确定审核通过？' % self.total_annul_amount
    #     elif self.flow_type == 'fail':
    #         self.display_info = '申请减免金额：%s，是否确定拒绝审核？' % self.total_annul_amount
    #     else:
    #         self.display_info = '111'



    def action_confirm(self):
        """
        确认按钮
        """
        examine_ids = self.env['loan.reduction.examine'].browse(self._context.get('active_ids'))
        # 根据是否批量审核及 同意/拒绝审核，更新审核状态
        if self.flow_type == 'batch' and self.batch_flow_type == 'audit' or self.flow_type == 'audit':
            if examine_ids[0].resource_model == 'collection':
                examine_ids.write({
                    'resource_model': 'loan',
                    'collection_flow_status': 'audit',
                    'collection_audit_time': datetime.now(),
                    'flow_type': 'draft',
                    'reduction_remark': self.remark
                })
            elif examine_ids[0].resource_model == 'loan':
                examine_ids.write({
                    'finance_audit_date': datetime.now(),
                    'flow_type': 'audit',
                    'finance_user_id': self.env.user.id,
                    'finance_user_char': self.env.user.name,
                    'finance_remark': self.remark
                })
                for examine_id in examine_ids:
                    # 如果为永久性减免或者有效期减免且当前时间小于有效期且剩余金额等于0
                    if examine_id.reduction_type == 'permanent' or examine_id.reduction_type == 'validity_reduction' and datetime.now() <= examine_id.validity_date and examine_id.order_id.pending_amount - examine_id.derate_amount == 0:
                        value = {
                            'pending_amount': examine_id.order_id.pending_amount - examine_id.derate_amount,
                        }
                        if examine_id.order_id.pending_amount - examine_id.derate_amount == 0:
                            value['repayment_success_date'] = datetime.now()
                            value['order_status_id'] = self.env['order.status'].search([('code', '=', '7')])  # 还款成功
                        examine_id.order_id.sudo().write(value)
        elif self.flow_type == 'batch' and self.batch_flow_type == 'fail' or self.flow_type == 'fail':
            if examine_ids[0].resource_model == 'collection':
                examine_ids.write({
                    'resource_model': 'collection',
                    'collection_flow_status': 'fail',
                    'collection_audit_time': datetime.now(),
                    'flow_type': 'draft',
                    'reduction_remark': self.remark
                })
            elif examine_ids[0].resource_model == 'loan':
                examine_ids.write({
                    'finance_audit_date': datetime.now(),
                    'flow_type': 'fail',
                    'finance_user_id': self.env.user.id,
                    'finance_user_char': self.env.user.name,
                    'finance_remark': self.remark
                })
        # 最后创建审核记录
        examine_ids.create_examine_record()
