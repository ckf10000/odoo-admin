import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class BankAccount(models.Model):
    """
    class T_Bank_Account {
        //银行卡id
        int id;//int, key, ODOO standard
        //APPid
        int app_id;//int, not null, key of T_app
        //用户id
        int user_id;//int, not null, key of T_user
        String ifsc_code; // str, not null
        String account_no;//str, not null

        String encrypt_version;//str,be null if account_no is not encrypted

        String account_no_part;//str,not null.e.g.2861*****7391

        boolean default_flag;//bool, not null, be False initially
    }
    """
    _name = 'bank.account'
    _description = '银行账户'
    _inherit = ['loan.basic.model']
    _table = 'T_bank_account'

    app_id = fields.Integer(string='枚举编码')
    user_id = fields.Integer(string='用户id', index=True)
    ifsc_code = fields.Char(string='金融系统代码')
    account_no = fields.Char(string='账号')
    encrypt_version = fields.Char(string='加密版本')
    account_no_part = fields.Char(string='账号部分')
    default_flag = fields.Boolean(string='默认标志')