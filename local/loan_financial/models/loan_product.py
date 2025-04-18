import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = 'loan.product'

    payment_setting_id = fields.Many2one('payment.setting', string='放款/退款渠道')
    payment_way_id = fields.Many2one('payment.way', string="放款方式", related='payment_setting_id.payment_way_id')

    repayment_setting_id = fields.Many2one('payment.setting', string='还款渠道')
    repayment_way_id = fields.Many2one('payment.way', string="还款方式", related='repayment_setting_id.payment_way_id')