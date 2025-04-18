import logging
from odoo import models, fields, api, exceptions
from ..utils import config

_logger = logging.getLogger(__name__)


class LoanAppUpdateMode(models.Model):
    _name = 'loan.app.update.mode'
    _description = 'APP更新模式'
    _rec_name = 'mode_name'
    _table = 'T_app_update_mode'

    enum_code = fields.Integer(string='枚举编码', required=True)
    mode_name = fields.Char(string='模式名称', required=True)
    sequence = fields.Integer(string='排序', required=True)


class LoanVersion(models.Model):
    _name = 'loan.app.version'
    _description = 'app信息'
    _inherit = ['loan.basic.model']
    _rec_name = 'app_id'
    _order = "write_date desc"
    _table = 'T_app_version'

    app_id = fields.Many2one('loan.app', string='APP名称', required=True, index=True, auto_join=True)
    client_platform_id = fields.Many2one(
        'loan.platform', 
        string='客户端平台', 
        related='app_id.client_platform_id',
        store=True,
    )
    client_enum_code = fields.Integer(string='客户端枚举编码', related='client_platform_id.enum_code')
    status = fields.Boolean(string='状态', default=True)

    version = fields.Char(string='版本号', required=True)
    version_code = fields.Integer(string='版本号编号', required=True)
    download_url = fields.Char(string='下载地址', required=True)
    update_content = fields.Text(string='更新内容', required=True)
    update_mode_id = fields.Many2one('loan.app.update.mode', string='更新类型', required=True)
    update_mode_code = fields.Integer(string='更新类型编码', related='update_mode_id.enum_code', store=True)
    release_type = fields.Selection([('0', '即时发布'), ('1', '定时发布')], string='发布时间', default="0", required=True)
    release_time = fields.Datetime(string='定时发布时间')
    release_status = fields.Boolean(string='发布状态', compute='_compute_release_status', store=True)

    @api.depends('release_type', 'release_time')
    def _compute_release_status(self):
        for record in self:
            if record.release_type == '0':
                record.release_status = True
            elif record.release_type == '1':
                if record.release_time and record.release_time <= fields.Datetime.now():
                    record.release_status = True
                else:
                    record.release_status = False
            else:
                record.release_status = False



    
