import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class UserBlack(models.Model):
    _name = 'user.black'
    _description = 'UserBlack'
    _inherit = ['loan.basic.model', 'loan.base.fields']
    _table = 'T_user_black'

    app_id = fields.Many2one('loan.app', string='APP配置copy', required=True)
    user_id = fields.Many2one('loan.user', string='关联用户', required=True)
    phone_no = fields.Char(string='用户电话', required=True)
    equip_id = fields.Char(string='设备ID', required=True)
    encrypt_version = fields.Char(string='加密版本')