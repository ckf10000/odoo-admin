import logging
from odoo import models, fields, api, exceptions


class CollectionOrderStatus(models.Model):
    _name = 'collection.order.status'
    _description = '催收订单状态'
    _table = 'C_order_status'

    name = fields.Char(string='订单类型', required=True)
    code = fields.Char(string='订单编码')
