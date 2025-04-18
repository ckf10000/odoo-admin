import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class Platform(models.Model):
    """
    platform_name: string，not null，最大长度 = MAX_length_platform_name
    """
    _name = 'loan.platform'
    _description = '平台信息'
    _rec_name = 'platform_name'
    _table = 'T_client_platform'
    _order = 'sequence'

    platform_name = fields.Char(string='平台名称', required=True)
    enum_code = fields.Integer(string='平台编码', required=True)
    sequence = fields.Integer(string='排序', required=True)


class Package(models.Model):
    """
    package_name: string，not null，最大长度 = MAX_length_package_name
    platform_id: int, not null, T_platform 的 key
    """
    _name = 'loan.package'
    _description = 'app包'
    _rec_name = 'package_name'
    _table = 'T_package'

    package_name = fields.Char(string='包名', required=True)


class App(models.Model):
    """
    app_name: string，not null，最大长度 = MAX_length_app_name
    package_id: int, not null, T_package 的 key
    platform_id: int, not null, T_platform 的 key
    status: bool, not null，TRUE = 启用，FALSE = 停用
    """
    _name = 'loan.app'
    _description = 'app信息'
    _inherit = ['loan.basic.model']
    _rec_name = 'app_name'
    _table = 'T_app'

    app_code = fields.Char(string='APPID', required=True, index=True)
    app_name = fields.Char(string='APP名称', required=True, index=True)
    package = fields.Char(string='APP包名', required=True)

    client_platform_id = fields.Many2one(
        'loan.platform', 
        string='客户端平台', 
        required=True, 
        ondelete="restrict"
    )
    client_platform_code = fields.Integer(string='客户端编码', related='client_platform_id.enum_code', store=True)
    status = fields.Boolean(string='状态', default=True)


class LoanAppUpdateMode(models.Model):
    _name = 'loan.app.update.mode'
    _description = 'APP更新模式'
    _rec_name = 'mode_name'
    _table = 'T_app_update_mode'

    enum_code = fields.Integer(string='枚举编码', required=True)
    mode_name = fields.Char(string='模式名称', required=True)
    sequence = fields.Integer(string='排序', required=True)


class LoanAppVersion(models.Model):
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

    version = fields.Char(string='版本号', required=True)
    version_code = fields.Integer(string='版本号编号', required=True)
    download_url = fields.Char(string='下载地址', required=True)
    update_content = fields.Text(string='更新内容', required=True)
    update_mode_id = fields.Many2one('loan.app.update.mode', string='更新类型', required=True)
    release_type = fields.Selection([('0', '即时发布'), ('1', '定时发布')], string='发布时间', default="0", required=True)
    release_time = fields.Datetime(string='定时发布时间')
    status = fields.Boolean(string='状态', default=True)
