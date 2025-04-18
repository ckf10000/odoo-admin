import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class Repay(models.Model):
    _name = 'loan.repay'
    _description = 'Repay'
    _inherit = ['loan.basic.model', 'bill.base.fields']
    _table = 'T_repay'

    bill_id = fields.Many2one('loan.bill', required=True)
    product_id = fields.Many2one('loan.product', string='关联产品')
    matrix_id = fields.Many2one('joint.loan.matrix', string='共贷矩阵')
    repay_time = fields.Integer(string='花费时间', required=True)
    amount = fields.Float(string='金额', required=True)
