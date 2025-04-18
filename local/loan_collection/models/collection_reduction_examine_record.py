import logging
from odoo import models, fields, api, exceptions
from datetime import date, datetime


class CollectionAutoExamine(models.Model):
    _name = 'collection.auto.examine'
    _table = 'C_auto_examine'
    _description = '自动审核'

    auto_examine = fields.Boolean(string='是否自动审核', default=False)
    max_annul_amount = fields.Float(string='最大可减免金额', digits=(16, 2))

    def action_confirm(self):
        if self.auto_examine:
            if self.max_annul_amount <= 0:
                raise exceptions.ValidationError('请输入＞0的数值')
            else:
                # 催收部分
                examine_ids = self.env['loan.reduction.examine'].sudo().search([('collection_flow_status', '=', 'draft'),
                                                                                ('resource_model', '=', 'collection'),
                                                                                ('derate_amount', '<=', self.max_annul_amount)])
                if examine_ids:
                    examine_ids.write({
                        'resource_model': 'loan',
                        'collection_flow_status': 'audit',
                        'collection_audit_time': datetime.now(),
                        'flow_type': 'draft',
                        'reduction_remark': '系统通过'
                    })
                    examine_ids.create_examine_record()
                # 财务部分
                loan_examine_ids = self.env['loan.reduction.examine'].sudo().search([('flow_type', '=', 'draft'),
                                                                                     ('resource_model', '=', 'loan'),
                                                                                     ('derate_amount', '<=', self.max_annul_amount)])
                if loan_examine_ids:
                    loan_examine_ids.write({
                            'resource_model': 'loan',
                            # 'collection_flow_status': 'audit',
                            'finance_audit_date': datetime.now(),
                            'flow_type': 'audit',
                            'reduction_remark': '系统通过'
                        })
                    for examine_id in loan_examine_ids:
                        # 如果为永久性减免或者有效期减免且当前时间小于有效期且剩余金额等于0
                        if examine_id.reduction_type == 'permanent' or examine_id.reduction_type == 'validity_reduction' and datetime.now() <= examine_id.validity_date and examine_id.order_id.pending_amount - examine_id.derate_amount == 0:
                            value = {
                                'pending_amount': examine_id.order_id.pending_amount - examine_id.derate_amount,
                            }
                            if examine_id.order_id.pending_amount - examine_id.derate_amount == 0:
                                value['repayment_success_date'] = datetime.now()
                                value['order_status_id'] = self.env['order.status'].search([('code', '=', '7')]) # 还款成功
                            examine_id.order_id.sudo().write(value)

                    loan_examine_ids.create_examine_record()


class CollectionReductionExamineRecord(models.Model):
    _name = 'collection.reduction.examine.record'
    _inherit = ['loan.reduction.examine']
    _table = 'C_reduction_examine_record'
    _description = '金额减免记录'

    collection_examine_id = fields.Many2one('loan.reduction.examine', string='金额减免审核')

    finance_audit_date = fields.Datetime(string='财务审核时间')
    finance_user_id = fields.Many2one('loan.user', string='财务审核人')
    finance_user_char = fields.Char(string='财务审核人', default='自动审核', help='是否自动审核')
    auto_result = fields.Boolean(string='审核结果')
    reduction_remark = fields.Text(string='催收备注')
    finance_remark = fields.Text(string='财务备注')

    def action_server_collection_reduction_record(self):
        """
        金额减免记录
        """
        context = self.env.context
        tree_view_id = self.env.ref('loan_collection.collection_reduction_examine_record_list')
        domain = [('collection_flow_status', '!=', 'draft'), ('resource_model', '=', 'collection')]
        search_view_id = self.env.ref('loan_collection.collection_reduction_examine_record_search')
        action_id = self.env.ref('loan_collection.collection_reduction_examine_record_action')
        return {
            'id': action_id.id,
            'type': 'ir.actions.act_window',
            'name': '金额减免管理',
            'res_model': self._name,
            'view_mode': 'tree',
            'domain': domain,
            'views': [(tree_view_id.id, 'list')],
            'search_view_id': [search_view_id.id],
            'target': 'current',
            'context': dict(context)
        }
