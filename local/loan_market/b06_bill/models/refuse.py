import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class LoanRefuse(models.Model):
    _name = 'loan.refuse'
    _description = 'Refuse'
    _inherit = ['loan.basic.model', 'bill.base.fields']
    _table = 'T_refuse'

    """
    app_id: int, not null, key of T_app
     user_id: int, not null, key of T_user
     user_phone: str, not null, redundancy from T_user
     bill_id: int, not null, key of T_bill
     product_id: int, not null, key of T_product

     refuse_time: long, not null
     refuse_code: int(see Enum_refuse_cause), not null
    """

    bill_id = fields.Many2one('loan.bill', required=True)
    product_id = fields.Many2one('loan.product', string='关联产品', related="bill_id.product_id", store=True)
    refuse_time = fields.Integer(required=True)
    refuse_code = fields.Integer(string='编码', required=True)