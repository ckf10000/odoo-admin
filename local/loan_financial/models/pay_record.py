import logging
from typing import Dict, List
from odoo import models, fields, api
from . import enums


_logger = logging.getLogger(__name__)


class PayRecord(models.Model):
    _name = 'pay.record'
    _description = '放款记录'
    _inherit = ['loan.basic.model']
    _table = 'F_pay_record'

    pay_order_id = fields.Many2one('pay.order', string='放款订单', auto_join=True, required=True, index=True)
    loan_order_id = fields.Many2one('loan.order', string='贷款订单', related="pay_order_id.order_id")
    order_no = fields.Char(string='订单号', related="pay_order_id.order_no")
    product_id = fields.Many2one('loan.product', string='产品', related="pay_order_id.product_id")

    payment_setting_id = fields.Many2one('payment.setting', string='放款渠道')
    payment_way_id = fields.Many2one('payment.way', string='放款方式')
    platform_order_no = fields.Char(string='平台订单号') # 放款序列号
    merchant_order_no = fields.Char(string='商户订单号') # 支付ID

    amount = fields.Float(string='放款金额', digits=(16, 2), default=0.0)
    fee = fields.Float(string='手续费', digits=(16, 2), default=0.0)
    tax = fields.Float(string='税费', digits=(16, 2), default=0.0)
    is_success = fields.Boolean(string='是否成功', required=True)
    fail_reason = fields.Char(string='失败原因')
    data = fields.Json(string='支付接口数据')

