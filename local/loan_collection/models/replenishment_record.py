import logging
from odoo import models, fields, api, exceptions
from datetime import datetime, date
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from . import enums

class ReplenishmentRecord(models.Model):
    _name = 'replenishment.record'
    _inherit = ['loan.basic.model']
    _description = '补单记录'

    loan_order_id = fields.Many2one('loan.order', string='关联订单')
    user_id = fields.Many2one('loan.user', string='关联用户', related="loan_order_id.loan_user_id", store=True)
    order_no = fields.Char(string='订单编号', related="loan_order_id.order_no", store=True)
    name = fields.Char(string='姓名', related="loan_order_id.loan_user_name", store=True)
    #order_type_id = fields.Many2one('order.type', string='订单类型', related="loan_order_id.order_type", store=True)
    order_type = fields.Selection(selection=enums.ORDER_TYPE, string='订单类型', related="loan_order_id.order_type", store=True)
    phone_no = fields.Char(string='手机号码', related="loan_order_id.loan_user_phone", store=True)
    business_type = fields.Selection([('repayment', '还款补单'), ('renewal', '展期补单')], string='业务类型')
    replenishment_time = fields.Datetime(string='补单时间')
    replenishment_amount = fields.Float(string='补单金额', digits=(16, 2))
    utr = fields.Char(string='UTR')
    voucher_file_ids = fields.Many2many('ir.attachment', string='凭证')
    status = fields.Selection([('pending', '待处理'),
                              ('process', '处理中'),
                              ('received', '已到账'),
                              ('closed', '已关闭')], string='状态')
    audit_user_id = fields.Many2one('res.users', string='审核人')
    application_user_id = fields.Many2one('res.users', string='申请人')
    close_reason = fields.Char(string='关单原因')

    def action_server_replenishment_record(self):
        """
        补单记录action
        """

        context = self.env.context
        tree_view_id = self.env.ref('loan_collection.replenishment_record_list')
        search_view_id = self.env.ref('loan_collection.replenishment_record_search')
        action_id = self.env.ref('loan_collection.replenishment_record_action')
        return {
            'id': action_id.id,
            'type': 'ir.actions.act_window',
            'name': '补单记录',
            'res_model': self._name,
            'view_mode': 'tree',
            'views': [(tree_view_id.id, 'list')],
            'search_view_id': [search_view_id.id],
            'target': 'current',
            'context': dict(context)
        }

    def action_upload_voucher(self):
        """
        上传凭证
        """
        context = self.env.context
        form_view_id = self.env.ref('loan_collection.replenishment_record_form2')
        return {
            'name': '上传凭证',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(form_view_id.id, 'form')],
            'target': 'new',
            'context': {
                'default_loan_order_id': context.get('order_id', 0),
                'default_status': 'pending',
                'default_application_user_id': self.env.user.id,
                'dialog_size': self._action_default_size(), **self._action_default_data()}
        }