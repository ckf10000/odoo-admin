import logging
from odoo import models, fields, api, exceptions


class LoanBaseFields(models.AbstractModel):
    _name = 'bill.base.fields'
    _description = '基本字段'

    user_id = fields.Many2one('loan.user', string='关联用户', required=True)
    app_id = fields.Many2one('loan.app', string='APP', required=True, related="user_id.app_id", store=True)
    user_phone = fields.Char(string='用户电话', required=True, related="user_id.phone_no", store=True)