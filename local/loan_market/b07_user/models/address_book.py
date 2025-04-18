import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class UserAddressBook(models.Model):
    _name = 'user.address.book'
    _description = '用户通讯录'
    _inherit = ['loan.basic.model']
    _table = 'T_address_book'

    
    user_id = fields.Many2one('loan.user', string='User', required=True)
    app_id = fields.Many2one('loan.app', string='App', related="user_id.app_id", store=True)

    timestamp = fields.Integer(string='上传时间')



class UserAddressBookItem(models.Model):
    _name = 'user.address.book.item'
    _description = '用户通讯录成员'
    _inherit = ['loan.basic.model']
    _table = 'T_address_book_item'

    addr_id = fields.Many2one('user.address.book', string='User')

    names = fields.Char(string='姓名')
    plain_text = fields.Char(string='未加密的手机号码')
    encrypted_text = fields.Char(string='加密的手机号码')
