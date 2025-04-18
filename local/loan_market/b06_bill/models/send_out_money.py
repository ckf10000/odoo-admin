import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class SendOutMoney(models.Model):
    _name = 'send.out.money'
    _description = 'SendOutMoney'
    _inherit = ['loan.basic.model', 'bill.base.fields']
    _table = 'T_send_out_money'

    bill_id = fields.Many2one('loan.bill', string='关联账单', required=True)
    product_id = fields.Many2one('loan.product', string='关联产品', related='bill_id.product_id', store=True)
    send_out_time = fields.Integer(string='发送时间', required=True)
    amount = fields.Float(string='金额', required=True)