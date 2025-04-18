import logging
import time, datetime, pytz
from typing import Dict, List
from odoo import models, fields, api, exceptions
from . import enums
from ..utils import date_utils, pay_utils


_logger = logging.getLogger(__name__)


class RefundRecord(models.Model):
    _name = 'refund.record'
    _description = '退款记录'
    _inherit = ['loan.basic.model']
    _table = 'F_refund_record'
    _order = 'refund_apply_time desc'

    order_id = fields.Many2one('loan.order', string='订单编号', auto_join=True, index=True)
    loan_period = fields.Integer(string='借款期限', related="order_id.loan_period")
    loan_apply_time = fields.Datetime('申请时间', related="order_id.apply_time")
    loan_user_unrepay_order_count = fields.Integer(string='未还订单数', related="order_id.loan_user_unrepay_order_count")

    order_no = fields.Char(string='订单编号', compute="_compute_from_order")
    order_type = fields.Selection(selection=enums.ORDER_TYPE, string='订单类型', compute="_compute_from_order")
    product_id = fields.Many2one('loan.product', string='产品名称', compute="_compute_from_order")
    contract_amount = fields.Float(string='合同金额', compute="_compute_from_order")

    refund_type = fields.Selection(selection=enums.REFUND_TYPE, string='退款类型')
    status = fields.Selection(enums.REFUND_STATUS, string='状态')

    loan_uid = fields.Integer('UserID')
    loan_user_name = fields.Char(string='姓名')
    loan_user_phone = fields.Char(string='手机号码')
    bank_name = fields.Char(string='收款银行')
    bank_account_no = fields.Char(string='收款账号')
    bank_ifsc_code = fields.Char(string='IFSC code')
    platform_profit = fields.Float('平台额外收益') 
    payment_setting_id = fields.Many2one('payment.setting', string="退款渠道", domain="[('use_type', '=', '1')]")
    payment_way_id = fields.Many2one('payment.way', string="退款方式")

    refund_amount = fields.Float('退款金额', digits=(16, 2))
    refund_remark = fields.Text('备注')
    refund_user_id = fields.Many2one('res.users', string='退款申请人')
    refund_apply_time = fields.Datetime('退款时间') # 退款申请时间

    refund_complete_time = fields.Datetime('退款完成时间') # 对接支付, 获取结果时间
    refund_fee = fields.Float('退款手续费', digits=(16, 2), default=0)
    refund_tax = fields.Float('退款税收', digits=(16, 2), default=0)
    platform_order_no = fields.Char(string='退款序列号')
    merchant_order_no = fields.Char(string='支付ID')
    refund_count = fields.Integer('退款次数', default=0)
    real_refund_amount = fields.Float('实际出账金额', compute="_compute_real_refund_amount", store=True)
    refund_fail_reason = fields.Text('退款失败原因')

    refuse_user_id = fields.Many2one('res.users', string='退款拒绝人')
    refuse_reason = fields.Text(string='拒绝原因')
    refuse_time = fields.Datetime(string='拒绝时间')

    wait_duration = fields.Char('未处理时长', compute='_compute_wait_duration')
    wait_duration_tip = fields.Boolean('是否高亮提示',compute='_compute_wait_duration')
    refund_voucher = fields.Char('退款凭证描述', compute="_compute_refund_voucher")

    @api.depends('order_id')
    def _compute_from_order(self):
        """
        a. 退款类型为“正常退款”的记录，显示订单生成时确定的订单编号；
        b.退款类型为“手动退款”的记录，订单编号显示为“-”；
        """
        for rec in self:
            if rec.refund_type == "1":
                rec.order_no = rec.order_id.order_no
                rec.order_type = rec.order_id.order_type
                rec.product_id = rec.order_id.product_id
                rec.contract_amount = rec.order_id.contract_amount
                rec.platform_profit = rec.order_id.platform_profit
            else:
                rec.order_no = ""
                rec.order_type = None
                rec.product_id = None
                rec.contract_amount = None
                rec.platform_profit = None

    @api.depends('status', 'refund_apply_time')
    def _compute_wait_duration(self):
        now = int(time.time())
        for order in self:
            if order.status == "2":
                start = order.refund_apply_time
            elif order.status in ("3", "4"):
                start = order.refund_complete_time
            else:
                order.wait_duration = ""
                order.wait_duration_tip = False
                continue

            start_timestamp = int(start.timestamp())
            duration, unit = date_utils.compute_timestamp_duration(start_timestamp, now)
            if unit == "min":
                order.wait_duration = f"{duration}min"
                order.wait_duration_tip = False
            else:
                order.wait_duration = f"{duration}h"
                if duration > 24:
                    order.wait_duration_tip = True
                else:
                    order.wait_duration_tip = False

    @api.depends('refund_amount', 'refund_fee', 'refund_tax')
    def _compute_real_refund_amount(self):
        for order in self:
            order.real_refund_amount = round(order.refund_amount + order.refund_fee + order.refund_tax, 2)

    @api.depends()
    def _compute_refund_voucher(self):
        for order in self:
            order.refund_voucher = "Refund"

    @api.onchange('loan_user_phone')
    def _onchange_loan_user_phone(self):
        # 正常退款不需要查询用户信息
        if self.refund_type == "1":
            return 
        
        if self.loan_user_phone:
            loan_user = self.env['loan.user'].search([('phone_no', '=', self.loan_user_phone)], limit=1)
            if not loan_user:
                self.loan_user_phone = None
                return {'warning': {'title': '提示', 'message': '手机号码输入错误，或用户不存在'}}
            self.loan_uid = loan_user.id
            self.loan_user_name = loan_user.name

    @api.model
    def create(self, vals):
        if vals.get('refund_type','1') == '1' and vals.get("refund_amount", 0) > vals.get("platform_profit", 0):
            raise exceptions.UserError("0<退款金额≤平台额外收益, 请输入正确数值")
        vals.update({
            "refund_user_id": self.env.user.id,
            "refund_apply_time": fields.Datetime.now()
        })
        obj = super().create(vals)

        obj.call_pay_handler()
        return obj
    
    def write(self, vals):
        if "refuse_reason" in vals:
            vals.update({
                "status": "5",
                "refuse_user_id": self.env.user.id,
                "refuse_time": fields.Datetime.now()
            })
        return super().write(vals)

    def call_pay_handler(self):
        """
        调用放款接口
        """
        if not self.refund_amount or not self.payment_setting_id:
            return
        refund_order_data = {'status': '2'}

        now = datetime.datetime.now()
        payment_channel = self.payment_setting_id.payment_channel_id
        trade_no = self.env['ir.sequence'].next_by_code('trade_record_no_seq')
        trade_status = "1"
        fail_reason = ""
        if payment_channel.enum_code == 2:
            params = {
                'type': 1,
                'mchId': int(payment_channel.merchant_no),
                'key': payment_channel.merchant_key,
                'productId': 27,
                'mchOrderNo': trade_no,
                'orderAmount': int(self.refund_amount*100),
                'notifyUrl': payment_channel.call_back_url,
                'clientIp': '127.0.0.1',
                'device': 'pc',
                'uid': self.loan_uid,
                'customerName': self.loan_user_name,
                'tel': self.loan_user_phone,
                'email': 'test@gmail.com',
                'returnType': 'json',
                'accountname': self.loan_user_name,
                'cardnumber': self.bank_account_no,
                'ifsc': self.bank_ifsc_code,
                'bankname': 'wavepay',
                'mode': 'IMPS',
            } 
            trade_data = pay_utils.coin_pay.create_transfer_order(params)
            platform_order_no = trade_data.get('data', {}).get('payOrderId')
            if trade_data.get('code', 999) != 200:
                trade_status = "3"
                fail_reason = trade_data['message']
        else:
            params = {
                'merchantNo': payment_channel.merchant_no,
                'key': payment_channel.merchant_key,
                'orderNo': trade_no,  
                'amount': str(self.refund_amount),    
                'notifyUrl': payment_channel.call_back_url,
                'name': self.loan_user_name,
                'account': self.bank_account_no,
                'ifscCode': self.bank_ifsc_code,
                'timestamp': now.astimezone(tz=pytz.timezone( 'Asia/Kolkata' )).strftime('%Y-%m-%d %H:%M:%S')
            }
            trade_data = pay_utils.sf_pay.create_transfer_order(params)
            platform_order_no = trade_data.get("platformOrderNo")
            if trade_data['code'] != 0:
                trade_status = "3"
                fail_reason = trade_data['code']
            
        # 创建交易记录
        trade_data = {
            'order_id': self.order_id.id if self.order_id else None,
            'payment_setting_id': self.payment_setting_id.id,
            'payment_way_id': self.payment_way_id.id,
            'trade_amount': self.refund_amount,
            'trade_no': trade_no,
            'trade_status': trade_status,
            'trade_type': '2',
            'trade_start_time': now,
            'platform_order_no': platform_order_no,
            'trade_data': trade_data,
            'res_model': self._name,
            'res_id': self.id
        }
        self.env['payment.setting.trade.record'].create(trade_data)

        # 更新订单信息
        if trade_status == "3":
            refund_order_data.update({
                'status': '4',
                'refund_complete_time': now,
                "refund_fail_reason": fail_reason
            })
        self.write(refund_order_data)
        return 
    
    def create_platformflow(self, trade_record):
        """
        创建平台流水
        """
        # 资金流水
        base_data = {
            "order_id": self.order_id.id if self.order_id else None,
            "product_id": self.product_id.id if self.order_id else None,
            "payment_setting_id": trade_record.payment_setting_id.id,
            "payment_way_id": trade_record.payment_way_id.id,
            "flow_time": trade_record.trade_end_time
        }
        flow_data = []
        if trade_record.trade_amount:
            flow_data.append({
                "flow_type": enums.FLOW_TYPE[0][0],
                "flow_amount": trade_record.trade_amount,
                "trade_type": enums.TRADE_TYPE[13][0],
                **base_data
            })
        refund_fee = self.payment_setting_id.calc_fee(trade_record.trade_amount)
        if refund_fee:
            flow_data.append({
                **base_data,
                "flow_type": enums.FLOW_TYPE[0][0],
                "flow_amount": refund_fee,
                "trade_type": enums.TRADE_TYPE[14][0],
            })                    
        self.env['platform.flow'].create(flow_data)

    def after_payment(self, trade_record):
        """
        退款完成
        """  
        now = fields.Datetime.now()
        refund_order_data = {
            "platform_order_no": trade_record.platform_order_no,
            "merchant_order_no": trade_record.trade_no,
            "refund_complete_time": now,
        }
        if trade_record.trade_status == "2":
            # 支付状态
            refund_fee = self.payment_setting_id.calc_fee(trade_record.trade_amount)
            refund_order_data.update({
                "status": "3",
                "refund_complete_time": now,
                "refund_fee": refund_fee,
                "refund_tax": 0
            })
            self.write(refund_order_data)

            # 更新订单状态
            self.order_id.update_order_status(now)

            # 资金流水
            self.create_platformflow(trade_record)
            

        else:
            refund_order_data.update({
                "pay_status": "4",
                "fail_reason": trade_record.trade_data.get('message') if trade_record.trade_data else "退款失败",
            })
            self.write(refund_order_data)
        return 

    def action_show_voucher(self):
        """
        展示退款凭证
        """
        return {
            'name': '退款凭证',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.form_refund_voucher').id,
            'res_id': self.id,
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size()
            }
        }
    
    def action_download_voucher(self):
        """
        下载退款凭证
        """
        form_view_id = self.env.ref('loan_financial.form_refund_voucher')
        url = f"/download_order_refund_voucher?res_id={self.id}&res_model={self._name}&view_id={form_view_id.id}"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
    
    def action_refund_again(self):
        """
        重新发起退款
        """
        self.call_pay_handler()
        return
    
    def action_show_refuse_wizard(self):
        """
        拒绝退款向导
        """
        return {
                'name': '退款拒绝',
                'type': 'ir.actions.act_window',
                'res_model': "refund.record",
                'res_id': self.id,
                'view_mode': 'form',
                'view_id': self.env.ref('loan_financial.form_refuse_refund').id,
                'target': 'new',
                'context': {
                    'dialog_size': self._action_default_size()
                }
            }
    
    def action_show_update_bank_info_wizard(self):
        """
        修改账号向导
        """
        return {
            'name': '修改账户',
            'type': 'ir.actions.act_window',
            'res_model': "refund.record",
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.form_refund_update_bank').id,
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size()
            }
        }

    def test_refund(self):
        """
        测试退款
        """
        now = fields.Datetime.now()

        trade_no = self.env['ir.sequence'].next_by_code('trade_record_no_seq')
        trade_status = "2"
        platform_order_no = f"{int(now.timestamp()*1000)}"

        # 创建交易记录
        trade_data = {
            'order_id': self.order_id.id if self.order_id else None,
            'payment_setting_id': self.payment_setting_id.id,
            'payment_way_id': self.payment_way_id.id,
            'trade_amount': self.refund_amount,
            'trade_no': trade_no,
            'trade_status': trade_status,
            'trade_type': '2',
            'trade_start_time': now,
            'trade_end_time': now,
            'platform_order_no': platform_order_no,
            'trade_data': {},
            'res_model': self._name,
            'res_id': self.id
        }
        trade_record = self.env['payment.setting.trade.record'].create(trade_data)

        refund_fee = self.payment_setting_id.calc_fee(self.refund_amount)
        refund_order_data = {
            "platform_order_no": platform_order_no,
            "merchant_order_no":platform_order_no,
            "refund_complete_time": now,
            "status": "3",
            "refund_fee": refund_fee,
            "refund_tax": 0
        }
        self.write(refund_order_data)

        # 更新订单状态
        self.order_id.get_repay_order().update_repay_status(now)

        # 资金流水
        self.create_platformflow(trade_record)
        return