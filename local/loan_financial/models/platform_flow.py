import logging
from odoo import models, fields, api, exceptions
from . import enums

_logger = logging.getLogger(__name__)


class PlatFormFlow(models.Model):
    _name = 'platform.flow'
    _description = 'PlatForm Flow'
    _inherit = ['loan.basic.model']
    _table = 'F_platform_flow'

    order_id = fields.Many2one('loan.order', string='订单', auto_join=True, index=True)
    order_no = fields.Char(related='order_id.order_no', store=True, index=True)
    order_type = fields.Selection(related='order_id.order_type', store=True)
    product_id = fields.Many2one('loan.product', related="order_id.product_id", store=True, index=True)
    payment_setting_id = fields.Many2one('payment.setting', string='交易渠道')
    payment_way_id = fields.Many2one('payment.way',string='交易方式')

    flow_type = fields.Selection(selection=enums.FLOW_TYPE, string='变动类型')
    flow_amount = fields.Float(string='变动金额', digits=(16, 2))
    trade_type = fields.Selection(selection=enums.TRADE_TYPE, string='交易类型')
    flow_time = fields.Datetime(string='变动时间')



