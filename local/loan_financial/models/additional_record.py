import logging
import datetime, pytz
from typing import Dict, List
from odoo import models, fields, api, exceptions
from . import enums
from ..utils import pay_utils


_logger = logging.getLogger(__name__)


class AdditionalRecord(models.Model):
    _name = 'additional.record'
    _description = '补单记录'
    _inherit = ['loan.basic.model']
    _table = 'F_additional_record'
    _order = 'apply_time desc'

    order_id = fields.Many2one('loan.order', string="财务订单", required=True, index=True, auto_join=True)
    repay_order_id = fields.Many2one('repay.order', string="还款订单", required=True, index=True, auto_join=True)
    order_no = fields.Char(string='订单编号', related="order_id.order_no")
    order_user_id = fields.Integer('UserID', related='order_id.loan_uid')
    order_user_name = fields.Char(string='姓名', related='order_id.loan_user_name')
    order_user_phone = fields.Char(string='手机号码', related="order_id.loan_user_phone")
    product_id = fields.Many2one('loan.product', string='产品名称', related="order_id.product_id")
    # order_apply_time = fields.Datetime(string='申请时间', related="order_id.apply_time")
    order_contract_amount = fields.Float(string='合同金额', related="order_id.contract_amount")

    addition_type = fields.Selection(enums.ADDITION_TYPE, string="业务类型", default='1')
    status = fields.Selection(enums.ADDITION_STATUS, string="状态", required=True)
    is_process = fields.Boolean('是否已处理', compute="_compute_is_process")
    
    utr = fields.Char('UTR', required=True)
    amount = fields.Float('补单金额')
    apply_time = fields.Datetime('申请时间', required=True, default=fields.Datetime.now)
    apply_user_id = fields.Many2one('res.users', string="申请人", default=lambda self: self.env.user)
    
    approval_user_id = fields.Many2one('res.users', string="审核人")
    approval_time = fields.Datetime('审核时间')
    close_reason = fields.Char('关单原因')
    close_reason_id = fields.Many2one('additional.record.close.reason', string='关联关单原因', ondelete="set null")

    payment_setting_id = fields.Many2one('payment.setting', string='支付渠道', domain="[('use_type', '=', '2')]")
    platform_order_no = fields.Char(string='支付订单号')
    merchant_order_no = fields.Char(string='支付ID')
    update_time = fields.Datetime('支付完成时间', default=fields.Datetime.now)

    attachment_id = fields.Many2one(
		'ir.attachment',
		'凭证图片',
		compute="_compute_attachment_id",
		store=True
	)
    voucher_img = fields.Image(string='凭证')

    @api.depends('status')
    def _compute_is_process(self):
        for record in self:
            record.is_process = False if record.status == '1' else True
    
    @api.depends('voucher_img')
    def _compute_attachment_id(self):
        for record in self:
            record.attachment_id = None
            if record.voucher_img:
                attachment_id = self.env['ir.attachment'].search([("res_model", "=", "additional.record"), ("res_id", "=", record.id), ('res_field', '=', 'voucher_img')], limit=1)
                if attachment_id:
                    record.attachment_id = attachment_id.id
    
    @api.model
    def create(self, vals):
        if vals.get('addition_type') == "2":
            order = self.env['loan.order'].search([('id', '=', vals.get('order_id'))])
            if not order._check_order_can_extension():
                raise exceptions.ValidationError('该订单不能进行展期补单')
                return
            
        if vals.get('amount') <= 0:
            raise exceptions.ValidationError('补单金额必须大于0')
        
        vals['status'] = '1'
        obj = super(AdditionalRecord, self).create(vals)
        return obj
    
    @api.onchange('close_reason_id')
    def onchange_close_reason_id(self):
        if self.close_reason_id:
            self.close_reason = self.close_reason_id.text
        else:
            self.close_reason = ''

    def action_show_additional_record(self):
        return {
            'name': '补单记录' if self.env.user.lang == "zh_CN" else "Reorder Record",
            'type': 'ir.actions.act_window',
            'res_model': "repay.order",
            'res_id': self.repay_order_id.id,
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.form_order_additional_record').id,
            'target': 'new',
            'context': {
            }
        }
    
    def action_show_update_payment_setting(self):
        """
        审核通过-选择支付渠道
        """
        return {
            'name': '审核通过',
            'type': 'ir.actions.act_window',
            'res_model': "additional.record",
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.form_additional_record_pass').id,
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size(), 
            }
        }
    
    def action_approval_pass(self):
        """
        审核通过
        1, 创建还款记录, 获取支付订单号
        2, 将支付订单号+填写的utr, 调用补单接口,获取补单结果
        """
        now = fields.Datetime.now()
        trade_data, pay_url = self.payment_setting_id.payment_channel_id.call_pay_order(self.amount, self.order_id)
        is_success, data = self.payment_setting_id.payment_channel_id.call_supplement_order(self.utr, trade_data["trade_no"])

        trade_no = trade_data["trade_no"]
        self.write({
            'status': '3' if is_success else '2',
            "update_time": now if is_success else None,
            'approval_user_id': self.env.user.id,
            'approval_time': now,
            'platform_order_no': trade_data.get("platform_order_no"),
            'merchant_order_no': trade_no
        })

        # 创建交易记录
        trade_data = {
            'order_id': self.order_id.id,
            'payment_setting_id': self.payment_setting_id.id,
            # 'payment_way_id': self.order_id.repayment_way_id.id,
            'trade_amount': self.amount,
            'trade_no': trade_no,
            'trade_status': "2" if is_success else "3",
            'trade_type': '1',
            'trade_start_time': now,
            'trade_end_time': now,
            'platform_order_no': trade_data.get("platform_order_no"),
            'trade_data': {
                "res_1": trade_data.get('trade_data'),
                "res_2": data
            },
            'res_model': self._name,
            'res_id': self.id
        }
        trade_record = self.env['payment.setting.trade.record'].create(trade_data)

        if not is_success:
            return 
        
        if self.addition_type == '1':
            self.repay_order_id.after_payment(trade_record)
        else:
            self.env["extension.record"].update_or_create_from_additional(trade_record)

    def action_show_close_record(self):
        """
        打开选择关单原因界面
        """
        return {
            'name': '关闭补单申请',
            'type': 'ir.actions.act_window',
            'res_model': "additional.record",
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.form_additional_record_close').id,
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size(), 
            }
        }

    def action_close_record(self):
        """
        确认关闭记录
        """
        self.write({
            'status': '4',
            'approval_user_id': self.env.user.id,
            'approval_time': fields.Datetime.now()
        })
        
    def action_test_pay(self):
        """
        模拟支付补单费用
        """
        now = fields.Datetime.now()
        self.write({
            'status': '3',
            'approval_user_id': self.env.user.id,
            'approval_time': now,
            "update_time": now
        })

        trade_no = self.env['ir.sequence'].next_by_code('trade_record_no_seq')
        
        # 创建交易记录
        trade_data = {
            'order_id': self.order_id.id,
            'payment_setting_id': self.payment_setting_id.id,
            # 'payment_way_id': self.order_id.repayment_way_id.id,
            'trade_amount': self.amount,
            'trade_no': trade_no,
            'trade_status': "2",
            'trade_type': '1',
            'trade_start_time': now,
            'trade_end_time': now,
            'platform_order_no': "",
            'trade_data': {},
            'res_model': self._name,
            'res_id': self.id
        }
        trade_record = self.env['payment.setting.trade.record'].create(trade_data)
        
        if self.addition_type == '1':
            self.repay_order_id.after_payment(trade_record)
        else:
            self.env["extension.record"].update_or_create_from_additional(trade_record)


class AdditionalRecordCloseReason(models.Model):
    _name = 'additional.record.close.reason'
    _description = '补单关闭原因'
    _inherit = ['loan.basic.model']
    _table = 'F_additional_record_close_reason'
    _rec_name = 'text'
    _order = 'sequence'
    
    text = fields.Char(string='原因')
    sequence = fields.Integer(string='排序', default=0)
    

    def test(self):
        pass

