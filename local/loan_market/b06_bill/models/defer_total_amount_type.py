import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class DeferTotalAmountType(models.Model):
    _name = 'defer.total.amount.type'
    _description = 'DeferTotalAmountType'
    _inherit = ['loan.basic.model']
    _table = 'T_defer_total_amount_type'
    _rec_name = 'type_name'
    _order = 'sequence'

    enum_code = fields.Integer(string='枚举编码', required=True)
    type_name = fields.Char(string='模式名称', required=True)
    sequence = fields.Integer(string='排序', required=True)