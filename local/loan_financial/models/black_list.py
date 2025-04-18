import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class BlackList(models.Model):
    _name = 'black.list'
    _description = 'Black User List'
    _inherit = ['loan.basic.model']
    _table = 'F_black_list'

    phone_no = fields.Char(string='手机号码', required=True, index=True)
    user_name = fields.Char(string='姓名', index=True)
    id_card_no = fields.Char(string='身份证号码')
    bank_account_no = fields.Char(string='银行卡号')
    reason = fields.Text(string='原因')