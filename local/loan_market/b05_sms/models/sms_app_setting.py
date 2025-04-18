import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class SmsAppSetting(models.Model):
    _name = 'sms.app.setting'
    _description = 'APP短信配置'
    _inherit = ['loan.basic.model']
    _order = 'write_date desc'
    _table = 'T_sms_app_setting'

    # sms_name = fields.Char(string='短信名称', required=True)
    template_id = fields.Many2one('loan.sms.template', string='短信名称', required=True)

    channel_type_id = fields.Many2one('sms.channel.type', string='渠道类型', related="template_id.channel_type_id", store=True)
    channel_type_code = fields.Integer(related='channel_type_id.enum_code', string='渠道类型编码', store=True)

    # send_mode = fields.Selection([('0', '即时发送'), ('1', '定时发送')], string='发送方式', required=True)
    # send_mode_daily_param = fields.Char(string='定时发送参数')

    template = fields.Text(string='模板内容', required=True)
    template_params = fields.Json(string='模板参数')
    status = fields.Boolean(string='状态', required=True, default=True)

    app_ids = fields.Many2many(
        'loan.app',
        'T_sms_app_relation',
        'app_sms_setting_id',
        'app_id',
        string='APP名称'
    )

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            # self.channel_type_code_id = self.template_id.channel_type_code_id
            self.template = self.template_id.content

    @api.model
    def _check_data(self, data):
        """
        检查数据, 并一次性抛出所有错误
        """
        # errors = []
        # exist_name = {}
        # for record in self.search([]):
        #     exist_name.setdefault(record.sms_name, []).append(record.id)

        # ids = exist_name.get(data.get('sms_name'))
        # if ids and ids[0] != data.get('id'):
        #     errors.append('短信名称已使用，请更换名称')

        # if errors:
        #     raise exceptions.ValidationError(self.format_action_error(errors))


