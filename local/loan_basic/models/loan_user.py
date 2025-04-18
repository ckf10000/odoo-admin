import logging
from odoo import models, fields, api, exceptions
from . import enums

_logger = logging.getLogger(__name__)


class LoanUser(models.Model):
    _name = 'loan.user'
    _description = 'LoanUser'
    _inherit = ['loan.basic.model']
    _table = 'T_user'

    app_id = fields.Many2one('loan.app', string='APP配置copy')
    phone_no = fields.Char(string='电话')
    encrypted_psw = fields.Char(string='加密')
    encrypt_version = fields.Char(string='加密版本')

    loan_order_ids = fields.One2many('loan.order', 'loan_user_id', string='订单')
    unrepay_order_count = fields.Integer(string='订单数量', compute='_compute_unrepay_order_count', store=True)
    name = fields.Char(string="姓名")
    
    @api.depends('loan_order_ids.order_status')
    def _compute_unrepay_order_count(self):
        for rec in self:
            rec.unrepay_order_count = len(rec.loan_order_ids.filtered(lambda x: x.order_status == "7"))