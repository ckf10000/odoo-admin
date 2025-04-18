import logging
from odoo import models, fields, api, exceptions


class LoanBaseFields(models.AbstractModel):
    _name = 'loan.base.fields'
    _description = '基本字段'

    app_id = fields.Many2one('loan.app', string='APP配置copy', index=True)
    user_id = fields.Many2one('loan.user', string='关联用户', index=True)
    phone_no = fields.Char(string='用户电话', index=True)
    equip_id = fields.Char(string='设备ID')
    encrypt_version = fields.Char(string='加密版本')