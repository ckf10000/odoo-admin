import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class UrgeTargetType(models.Model):
    _name = 'sms.urge.target.type'
    _description = '催收短信发送对象'
    _rec_name = 'type_name'
    _order = 'sequence'
    _table = 'T_sms_urge_target_type'

    enum_code = fields.Integer(string='枚举编码', required=True)
    type_name = fields.Char(string='模式名称', required=True)
    sequence = fields.Integer(string='排序', required=True)


class SmsUrgeSetting(models.Model):
    _name = 'sms.urge.setting'
    _description = '催收短信配置'
    _inherit = ['loan.basic.model']
    _order = 'write_date desc'
    _table = 'T_sms_urge_setting'

    sms_name = fields.Char(string='短信名称', required=True)
    channel_type_code_id = fields.Many2one('sms.channel.type', string='渠道类型', required=True)
    channel_type_code = fields.Integer(related='channel_type_code_id.enum_code', string='渠道类型编码', store=True)

    num_overdue_days = fields.Integer(string='逾期天数', required=True)

    sms_target_code_id = fields.Many2one('sms.urge.target.type', string='发送对象', required=True)
    sms_target_code = fields.Integer(related='sms_target_code_id.enum_code', string='发送对象编码', store=True)

    template = fields.Text(string='模板内容', required=True)
    template_params = fields.Json(string='模板参数')
    status = fields.Boolean(string='状态', required=True, default=True)

    product_ids = fields.Many2many(
        'loan.product',
        'T_sms_urge_relation',
        'urge_sms_setting_id',
        'product_id',
        string='产品名称'
    )

    @api.model
    def _check_data(self, data):
        """
        检查数据, 并一次性抛出所有错误
        """
        errors = []
        exist_name = {}
        for record in self.search([]):
            exist_name.setdefault(record.sms_name, []).append(record.id)

        ids = exist_name.get(data.get('sms_name'))
        if ids and ids[0] != data.get('id'):
            errors.append('短信名称已使用，请更换名称')

        if data.get('num_overdue_days') < -7:
            errors.append('逾期天数请输入≥-7的整数')

        if errors:
            raise exceptions.ValidationError(self.format_action_error(errors))



