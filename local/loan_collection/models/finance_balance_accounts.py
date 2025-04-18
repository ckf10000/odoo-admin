import logging
from odoo import models, fields, api, exceptions


class FinanceBalanceAccounts(models.Model):
    _inherit = 'loan.order'
    _description = '财务平账'

    balance_accounts = fields.Float(string='平账金额', digits=(16, 2))
    balance_time = fields.Datetime(string='平账时间')
    balance_type = fields.Selection([
        ('1', '对公转账'),
        ('2', '抹罚息')
    ], string='平账类型')
    penalty_interest_amount = fields.Float(string='抹罚息金额')
    contract_balance_amount = fields.Float(string='合同平账金额')
    balance_penalty_interest = fields.Float(string='平账罚息')
    balance_overdue_fine = fields.Float(string='平账滞纳金')
    balance_remove = fields.Float(string='平账备注')

    def action_server_reductio_record(self):
        """
        财务平账action
        """
        context = self.env.context
        repayment_status_id = self.env['repayment.status'].search([('code', '=', '1')])
        domain = [('repayment_status', '=', repayment_status_id.id)]
        tree_view_id = self.env.ref('loan_collection.loan_finance_balance_accounts_list')
        search_view_id = self.env.ref('loan_collection.loan_finance_balance_accounts_search')
        action_id = self.env.ref('loan_collection.loan_finance_balance_accounts_action')
        return {
            'id': action_id.id,
            'type': 'ir.actions.act_window',
            'name': '财务平账',
            'res_model': self._name,
            'domain': domain,
            'view_mode': 'tree',
            'views': [(tree_view_id.id, 'list')],
            'search_view_id': [search_view_id.id],
            'target': 'current',
            'context': dict(context)
        }

    def action_server_order_line(self):
        """
        财务平账明细
        """
        context = self.env.context
        repayment_status_id = self.env['repayment.status'].search([('code', '=', '1')])
        domain = [('repayment_status', '=', repayment_status_id.id)]
        tree_view_id = self.env.ref('loan_collection.loan_order_line_list')
        search_view_id = self.env.ref('loan_collection.loan_order_line_search')
        action_id = self.env.ref('loan_collection.loan_order_line_action')
        return {
            'id': action_id.id,
            'type': 'ir.actions.act_window',
            'name': '财务平账明细',
            'res_model': self._name,
            'view_mode': 'tree',
            'views': [(tree_view_id.id, 'list')],
            'search_view_id': [search_view_id.id],
            'target': 'current',
            'domain': domain,
            'context': dict(context)
        }




