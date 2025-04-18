import logging
from odoo import models, fields, api, exceptions




class LoanReductionExamineRecord(models.Model):
    _inherit = ['loan.reduction.examine']
    _description = '金额减免记录'

    finance_audit_date = fields.Datetime(string='财务审核时间')
    finance_user_id = fields.Many2one('loan.user', string='财务审核人')
    finance_user_char = fields.Char(string='财务审核人', default='自动审核', help='是否自动审核')
    auto_result = fields.Boolean(string='审核结果')
    reduction_remark = fields.Text(string='催收备注')
    finance_remark = fields.Text(string='财务备注')

    def action_server_reduction_record(self):
        """
        金额减免记录
        """
        context = self.env.context
        tree_view_id = self.env.ref('loan_collection.loan_reductio_record_list')
        domain = [('flow_type', '=', 'audit'), ('resource_model', '=', 'loan')]
        search_view_id = self.env.ref('loan_collection.loan_reductio_record_search')
        action_id = self.env.ref('loan_collection.loan_reductio_record_action')
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