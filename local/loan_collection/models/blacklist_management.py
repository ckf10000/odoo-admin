import logging
from odoo import models, fields, api, exceptions
from datetime import datetime, date
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class BlacklistManagement(models.Model):
    _name = 'blacklist.management'
    _inherit = ['loan.basic.model']
    _table = 'C_blacklist_management'
    _description = '黑名单管理'

    phone_no = fields.Char(string='手机号')
    name = fields.Char(string='姓名')
    id_no = fields.Char(string='身份证号')
    bank_card_no = fields.Char(string='银行卡号')
    reason = fields.Char(string='原因')
    dept_id = fields.Many2one('hr.department', string='所属部门', related='create_uid.department_id', store=True)

    excel_import_list = fields.Char(string='批量导入')

    def action_batch_import(self):
        """
        批量导入黑名单
        """
        # todo
        form_view_id = self.env.ref('loan_collection.blacklist_management_form2')
        return {
            'name': '批量导入',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(form_view_id.id, 'form')],
            'target': 'new',
            'context': {'dialog_size': self._action_default_size(), **self._action_default_data()}
        }

    def action_server_blacklist_management(self):
        """
        黑名单管理action
        """

        context = self.env.context
        tree_view_id = self.env.ref('loan_collection.blacklist_management_list')
        search_view_id = self.env.ref('loan_collection.blacklist_management_search')
        action_id = self.env.ref('loan_collection.blacklist_management_action')
        return {
            'id': action_id.id,
            'type': 'ir.actions.act_window',
            'name': '黑名单管理',
            'res_model': self._name,
            'view_mode': 'tree',
            'views': [(tree_view_id.id, 'list')],
            'search_view_id': [search_view_id.id],
            'target': 'current',
            'context': dict(context)
        }
