import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

 
class LoanOrderSettings(models.TransientModel):
    _name = 'loan.order.settings'
    _description = '财务订单配置'
    _inherit = ['loan.basic.model']
    _table = 'F_loan_order_settings'

    key = fields.Char(string='key', required=True, index=True)
    desc = fields.Char(string='描述')
    value = fields.Char(string='value', required=True)
    value_type = fields.Selection([
        ('str', '字符串'), 
        ('int', '整数'), 
        ('float', '浮点数'), 
        ('bool', '布尔值')
    ], string='value类型')
    
    
    @api.model
    def get_param(self, key, default=None):
        rec = self.search([('key', '=', key)], limit=1)
        value = rec.value if rec else default
        if rec.value_type == 'bool':
            value = value.lower() in ('true', '1')
        elif rec.value_type == 'int':
            value = int(value)
        elif rec.value_type == 'float':
            value = float(value)
        return value
    
    @api.model
    def set_param(self, key, value):
        rec = self.search([('key', '=', key)], limit=1)
        if rec:
            if rec.value_type == 'bool':
                if value in [1, '1', 'true', True]:
                    value = '1'
                else:
                    value = '0'
            rec.write({'value': value})