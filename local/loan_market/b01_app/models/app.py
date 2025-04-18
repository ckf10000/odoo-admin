import logging
from odoo import models, fields, api, exceptions
from ..utils import config

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

    platform_name = fields.Char(string='平台名称', required=True, size=config.PlatformConfig.MAX_length_platform_name)
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

    package_name = fields.Char(string='包名', required=True, size=config.PackageConfig.MAX_length_package_name)


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
    app_name = fields.Char(string='APP名称', required=True, index=True, size=config.AppConfig.MAX_length_app_name)
    # package_id = fields.Many2one('loan.package', string='APP包名', required=True, domain="['|', ('app_ids', '=', False), ('app_ids.active', '=', False)]", ondelete="restrict")
    # platform_id = fields.Many2one('loan.platform', string='平台', related='package_id.platform_id', store=True)
    package = fields.Char(string='APP包名', required=True)
    # client = fields.Selection(
    #     config.AppConfig.App_client, 
    #     string='客户端', 
    #     required=True,
    #     default=config.AppConfig.App_client[0][0]
    # )
    client_platform_id = fields.Many2one(
        'loan.platform', 
        string='客户端平台', 
        required=True, 
        ondelete="restrict"
    )
    client_platform_code = fields.Integer(string='客户端编码', related='client_platform_id.enum_code', store=True)
    status = fields.Boolean(string='状态', default=True)

    matrix_id = fields.Many2one('joint.loan.matrix', string='共贷矩阵', required=True, index=True, ondelete="restrict")

    copy_app_id = fields.Many2one('loan.app', string='APP配置copy', ondelete="set null")
    setting_ids = fields.One2many('loan.app.setting', 'app_id', string='设置')

    def _check_app_info(self):
        errors = []
        app_names = {}
        client_apps = {}

        # 不同客户端已存在的包名
        for app in self.search([]):
            app_names.setdefault(app.app_name, []).append(app.id)
            client_apps.setdefault(app.client_platform_id, set()).add(app.package)

        # app名称校验
        if len(app_names.get(self.app_name, [])) > 1:
            errors.append('该APP名称已使用, 请更换名称')
            # raise exceptions.ValidationError('该APP名称已使用，请更换名称')
        if self.app_name.count('  '):
            errors.append('APP名称中不能有连续空格, 请调整')
            # raise exceptions.ValidationError('APP名称中不能有连续空格，请调整')
        
        # 包名校验
        if self.package.count('  '):
            errors.append('APP包名中不能有连续空格, 请调整')
            # raise exceptions.ValidationError('APP包名中不能有连续空格，请调整')

        # 检查不同客户端是否重名
        exist = False
        for client_id in client_apps:
            if app.client_platform_id == client_id:
                continue

            packages = client_apps.get(client_id, [])
            if app.package in packages:
                exist = True
                break

        if exist:
            errors.append('不同客户端的APP包名不可重复')
            # raise exceptions.ValidationError('不同客户端的APP包名不可重复')
        if errors:
            raise exceptions.ValidationError('\n'.join(errors))

    def _init_app_config(self):
        if self.setting_ids:
            return 
        
        if self.copy_app_id:
            app_settings = [{
                "app_id": self.id,
                "setting_item_id": setting.setting_item_id.id,
                "item_value": setting.item_value
            } for setting in self.copy_app_id.setting_ids.filtered(lambda x: x.status)]
        else:
            app_settings = self.env['loan.app.setting.item']._get_app_dft_setting_items(self.id)
        self.env['loan.app.setting'].create(app_settings)

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            val['app_code'] = self.env['ir.sequence'].next_by_code('app_code_seq')
        objs = super().create(vals_list)

        # 创建应用配置
        for obj in objs:
            obj._check_app_info()
            obj._init_app_config()
        return objs
    
    def write(self, vals):
        res = super().write(vals)
        self._check_app_info()
        return res


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

    version = fields.Char(string='版本号', required=True)
    version_code = fields.Integer(string='版本号编号', required=True)
    download_url = fields.Char(string='下载地址', required=True)
    update_content = fields.Text(string='更新内容', required=True)
    update_mode_id = fields.Many2one('loan.app.update.mode', string='更新类型', required=True)
    release_type = fields.Selection([('1', '即时发布'), ('2', '定时发布')], string='发布时间', default="1", required=True)
    release_time = fields.Datetime(string='定时发布时间')
    status = fields.Boolean(string='状态', default=True)
