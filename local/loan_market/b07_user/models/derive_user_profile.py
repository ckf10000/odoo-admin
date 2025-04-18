import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class DeriveUserProfile(models.Model):
    _name = 'derive.user.profile'
    _description = 'DeriveUserProfile'
    _inherit = ['loan.basic.model']
    _table = 'T_derive_user_profile'

    app_id = fields.Many2one('loan.app', string='APP配置copy', required=True)
    matrix_id = fields.Many2one('loan.matrix', string='矩阵配置')
    user_id = fields.Many2one('loan.user', string='关联用户', required=True, index=True)
    phone_no = fields.Char(string='用户电话', required=True)
    encrypt_version = fields.Char(string='加密版本')

    # loan_repay_id = fields.Many2one('loan.repay')
    # loan_bill_id = fields.Many2one('loan.bill')
    # send_out_money_id = fields.Many2one('send.out.money')

    did_repay_flag = fields.Boolean()
    product_earliest_due_time = fields.Integer()
    fst_time_send_out = fields.Integer()
    last_action_code = fields.Integer()
    last_action_time = fields.Integer()
    hinted_version = fields.Char()
    new_customer = fields.Boolean()
    system_new_customer = fields.Boolean()