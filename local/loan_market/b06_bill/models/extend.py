import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)




class BillExtend(models.Model):
    """
    class T_extend {
        id: int, key, ODOO standard
        bill_id: int, not null, key of T_bill
        product_id: int, not null, key of T_product

        apply_time: long, not null
        extend_day_num: int, not null, 展期天数
        extend_fee: float, not null, 展期费用

        paid_time: long, maybe null, 成功支付展期费用的时间
        paid_amount: float, maybe null, 成功支付的金额

        status: int, not null， see ENUM_extend_status  TODO  咨询彭总
            // EnumCode_extend_status_applied (尚未支付展期费用)
            // EnumCode_extend_status_paid (已经支付展期费用)
            // TODO
    }
    """
    _name = 'bill.extend'
    _description = 'Bill Extend'
    _inherit = ['loan.basic.model']
    _table = 'T_extend'

    bill_id = fields.Integer(string='bill id')
    product_id = fields.Integer(string='product id', index=True)
    apply_time = fields.Integer(string='apply time')
    extend_day_num = fields.Integer(string='extend day num')
    extend_fee = fields.Float(string='extend fee')
    paid_time = fields.Integer(string='paid time')
    paid_amount = fields.Float(string='paid amount')
    status = fields.Integer(string='status')