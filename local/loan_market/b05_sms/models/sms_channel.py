import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class SmsChannelType(models.Model):
    _name = 'sms.channel.type'
    _description = '短信渠道类型'
    _rec_name = 'type_name'
    _order = 'sequence'
    _table = 'T_sms_channel_type'

    enum_code = fields.Integer(string='枚举编码', required=True)
    type_name = fields.Char(string='模式名称', required=True)
    sequence = fields.Integer(string='排序', required=True)


class SmsChannelSetting(models.Model):
    _name = 'sms.channel.setting'
    _description = '短信渠道'
    _inherit = ['loan.basic.model']
    _order = 'channel_type_id, priority desc'
    _table = 'T_sms_channel_setting'

    channel_name = fields.Char(string='渠道名称', required=True)
    channel_type_id = fields.Many2one('sms.channel.type', string='渠道类型', required=True)
    channel_type_code = fields.Integer(related='channel_type_id.enum_code', string='渠道类型编码', store=True)

    access_key = fields.Char(string='AccessKey', required=True)
    display_access_key = fields.Char(string='AccessKey', compute='_compute_display_access_key')
    access_secret = fields.Char(string='AccessSecret', required=True)
    display_access_secret = fields.Char(string='AccessSecret', compute='_compute_display_access_secret')

    priority = fields.Integer(string='优先级', required=True)
    status = fields.Boolean(string='状态', required=True, default=True)

    @api.depends('access_key')
    def _compute_display_access_key(self):
        for record in self:
            record.display_access_key = record.access_key[:5] + '***' + record.access_key[-3:]

    @api.depends('access_secret')
    def _compute_display_access_secret(self):
        for record in self:
            record.display_access_secret = record.access_secret[:5] + '***' + record.access_secret[-3:]

    @api.model
    def _check_data(self, data):
        """
        检查数据, 并一次性抛出所有错误
        """
        errors = []
        exist_name = {}
        exist_priority = {}
        for record in self.search([]):
            exist_name.setdefault(record.channel_name, []).append(record.id)
            exist_priority.setdefault(record.priority, []).append(record.id)

        ids = exist_name.get(data.get('channel_name'))
        if ids and ids[0] != data.get('id'):
            errors.append('该渠道名称已使用，请更换名称')

        priority = exist_priority.get(data.get('priority'))
        if priority and priority[0] != data.get('id'):
            errors.append('该渠道优先级已存在，请更换优先级')

        if errors:
            raise exceptions.ValidationError(self.format_action_error(errors))
