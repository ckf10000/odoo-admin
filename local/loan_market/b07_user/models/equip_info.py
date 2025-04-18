import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class EquipInfo(models.Model):
    _name = 'equip.info'
    _description = 'EquipInfo'
    _inherit = ['loan.basic.model', 'loan.base.fields']
    _table = 'T_equip_info'

    acquire_time = fields.Char(string='获取时间')
    gaid = fields.Char(string='设备id/谷歌 advertising id')
    android_id = fields.Char(string='安卓id')
    phone_os = fields.Char(string='手机操作系统')
    phone_model = fields.Char(string='手机型号')
    network_operator_name = fields.Char(string='网络运营商')
    network_type = fields.Char(string='网络类型')
    language = fields.Char(string='设备本地语言')
    brand = fields.Char(string='设备品牌')
    product_name = fields.Char(string='产品名称')
    sys_version = fields.Char(string='系统版本')
    android_sdk_version_code = fields.Char(string='安卓sdk版本')
    use_wifi_flag = fields.Boolean(string='是否使用wifi')
    use_vpn_flag = fields.Boolean(string='是否使用vpn')