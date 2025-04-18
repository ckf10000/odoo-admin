import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class LoanSmsTemplate(models.Model):
    _name = 'loan.sms.template'
    _description = '短信模板'
    _order = 'sequence'
    _table = 'T_sms_template'

    name = fields.Char(string='模板名称', required=True)
    channel_type_id = fields.Many2one('sms.channel.type', string='渠道类型', required=True)
    channel_type_code = fields.Integer(related='channel_type_id.enum_code', string='渠道类型编码', store=True)
    content = fields.Text(string='模板内容', required=True)
    sequence = fields.Integer(string='排序', required=True)
