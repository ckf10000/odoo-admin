import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class LoanUser(models.Model):
    _inherit = ['loan.user']

    app_id = fields.Many2one('loan.app', string='APP配置copy')
    phone_no = fields.Char(string='电话')
    encrypted_psw = fields.Char(string='加密')
    encrypt_version = fields.Char(string='加密版本')