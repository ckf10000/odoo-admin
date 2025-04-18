import logging
import datetime, pytz
from typing import Dict, List
from odoo import models, fields, api, exceptions
from . import enums
from ..utils import pay_utils


_logger = logging.getLogger(__name__)


class ExtensionRecord(models.Model):
    _name = 'extension.record'
    _description = '展期记录'
    _inherit = ['loan.basic.model']
    _table = 'F_extension_record'

    order_id = fields.Many2one('loan.order', string="订单编号", index=True, auto_join=True)
    order_no = fields.Char(string='订单编号', related="order_id.order_no")
    loan_uid = fields.Integer('UserID', related='order_id.loan_uid')
    loan_user_name = fields.Char(string='姓名', related='order_id.loan_user_name')
    loan_user_phone = fields.Char(string='手机号码', related="order_id.loan_user_phone")
    product_id = fields.Many2one('loan.product', string='产品名称', related="order_id.product_id")
    
    status = fields.Selection(selection=enums.EXTENSION_STATUS, string='展期状态', index=True)
    apply_time = fields.Datetime(string='展期申请时间', default=fields.Datetime.now, index=True)
    apply_user_id = fields.Many2one('res.users', string='申请用户', default=lambda self: self.env.user.id)
    success_time = fields.Datetime(string='展期成功时间')

    extension_days = fields.Integer(string='展期天数')
    extension_amount = fields.Float(string='展期费用', digits=(16, 2)) # 应付金额

    order_repay_date = fields.Date(string='原到期日')
    extension_repay_date = fields.Date(string='新到期日', compute='_compute_extension_date')
    extension_start_date = fields.Date(string='展期开始日期', compute='_compute_extension_date')
    extension_end_date = fields.Date(string='展期结束日期', compute='_compute_extension_date')

    repay_record_ids = fields.One2many('repay.record', 'extension_record_id', '还款记录')
    repayed_amount = fields.Float(string='实付金额', compute="_compute_repayed_amount") # 实付金额, 
    repayed_fee = fields.Float(string='展期手续费', compute="_compute_repayed_amount")
    repayed_tax = fields.Float(string='税收', compute="_compute_repayed_amount")
    repay_count = fields.Integer(string='展期还款次数', compute="_compute_repayed_amount")

    actual_entry_amount = fields.Float('实际入账金额', compute="_compute_actual_entry_amount")

    pending_amount = fields.Float('挂账金额', compute="_compute_pending_amount") # 待还金额

    platform_order_no = fields.Char(string='展期序列号')
    merchant_order_no = fields.Char(string='支付ID') 
    payment_setting_id = fields.Many2one('payment.setting', string='还款渠道')
    payment_way_id = fields.Many2one('payment.way',string='还款方式')
    platform_profit = fields.Float('平台额外收益', compute="_compute_platform_profit")

    
    # 平账
    settle_record_ids = fields.One2many('extension.settle.record', 'extension_record_id', '平账记录')
    settle_amount = fields.Float('平账金额', digits=(16, 2), compute='_compute_settle_amount')

    @api.depends('extension_days', 'success_time')
    def _compute_extension_date(self):
        """
        显示订单展期成功后，系统新生成的订单的应还时间（以“展期成功时间（含）”开始，推算出“展期天数”后的具体日期
        """
        for rec in self:
            if rec.status == "2":
                repay_date = rec.success_time + datetime.timedelta(days=rec.extension_days-1)
                rec.extension_repay_date = repay_date
                rec.extension_start_date = rec.success_time
                rec.extension_end_date = repay_date
            else:
                rec.extension_repay_date = False
                rec.extension_start_date = False
                rec.extension_end_date = False

    @api.depends('repay_record_ids.is_cancel', 'status')
    def _compute_repayed_amount(self):
        for order in self:
            if order.status == "5":
                order.repayed_amount = 0
                order.repayed_fee = 0
                order.repayed_tax = 0
                order.repay_count = 0
            else:
                records = order.repay_record_ids.filtered(lambda r: not r.is_cancel)
                order.repayed_amount = round(sum([i.amount for i in records]), 2)
                order.repayed_fee = round(sum([i.fee for i in records]), 2)
                order.repayed_tax = round(sum([i.tax for i in records]), 2)
                order.repay_count = len(records)

    @api.depends('settle_record_ids')
    def _compute_settle_amount(self):
        for order in self:
            order.settle_amount = round(sum([i.settle_amount for i in order.settle_record_ids]), 2)

    @api.depends('extension_amount', 'repayed_amount', 'settle_amount')
    def _compute_pending_amount(self):
        for order in self:
            pending_amount = round(order.extension_amount - order.repayed_amount - order.settle_amount, 2)
            order.pending_amount = pending_amount if pending_amount > 0 else 0

    @api.depends('repayed_amount', 'repayed_fee', 'repayed_tax')
    def _compute_actual_entry_amount(self):
        for order in self:
            order.actual_entry_amount = round(order.repayed_amount - order.repayed_fee - order.repayed_tax, 2)

    @api.depends('repayed_amount', 'extension_amount', 'settle_amount')
    def _compute_platform_profit(self):
        """
        平台额外收益=展期实付金额-展期应付金额+展期平账金额, 如果平台额外收益≤0, 则计为0
        """
        for rec in self:
            platform_profit = round(rec.repayed_amount - rec.extension_amount + rec.settle_amount, 2)
            rec.platform_profit = platform_profit if platform_profit > 0 else 0

    @api.model
    def create(self, vals):
        obj = super().create(vals)
        return obj
    
    @api.model
    def update_or_create_from_additional(self, trade_record):
        """
        根据展期补单，创建或更新展期记录
        """
        order = trade_record.order_id
        if order.order_status == "8":
            return
        
        rec = self.search([('order_id', '=', order.id), ('status', 'in', ['1', '3', '4'])], limit=1)
        pay_record_data = {
            "order_id": order.id,
            "repay_type": "2",
            "repay_time": trade_record.trade_end_time,
            "platform_order_no": trade_record.platform_order_no,
            "merchant_order_no": trade_record.trade_no,
            "payment_setting_id": trade_record.payment_setting_id.id,
            "payment_way_id": self.order_id.payment_way_id.id,
            "amount": trade_record.trade_amount,
            "fee": trade_record.payment_setting_id.calc_fee(trade_record.trade_amount),
            "tax": 0,
            "order_pending_amount": order.pending_amount
        }
        if not rec:
            rec = self.create({
                "order_id": order.id,
                "status": "1",
                "apply_time": trade_record.trade_end_time,
                "extension_days": order.loan_period,
                "extension_amount": order.compute_extension_amount(),
                "order_repay_date": order.repay_date,
                "repay_record_ids": [(0, 0, pay_record_data)]
            })
        else:
            pay_record_data["extension_record_id"] = rec.id
            rec.env['repay.record'].create(pay_record_data)

        rec.update_extension_status(trade_record.trade_end_time)
        return rec

    @api.model
    def task_close_extension(self):
        """
        展期成功(展期费支付完成)
        1. 关联财务订单状态改为还款完成
        2. 关联财务订单的还款订单状态改为还款完成
        3. 创建新的财务订单
        4. 创建新的财务订单的还款订单
        4. 创建新的贷超订单
        """
        now = fields.Datetime.now()
        expire_time = now.replace(hour=0, minute=0, second=0)
        for rec in self.search([('status', 'in', ['1', '3', '4']), ('apply_time', '<', expire_time)]):
            rec.close_extension()

    def close_extension(self):
        """
        关闭展期
        """
        amount = self.repayed_amount + self.settle_amount
        # 失效
        if not amount:
            self.write({'status': "6"})
            return True
        # 部分支付
        self.write({'status': "5"})
        # 展期还款记录转正常还款记录
        repay_order = self.order_id.get_repay_order()
        for i in self.repay_record_ids:
            repay_record_data = i._prepare_compute_vals({"amount": amount, "repay_order_id": repay_order.id, "repay_type": "1"})
            i.write(repay_record_data)
        
        # 展期平账转还款平账
        if self.settle_amount:
            self.env["settle.record"].create({
                "order_id": self.order_id.id,
                "repay_order_id": repay_order.id,
                "order_pending_amount": self.order_id.pending_amount,
                "order_overdue_fee": self.order_id.unpaid_overdue_fee,
                "amount": self.settle_amount,
                "overdue_amount": 0,
                "settle_time": fields.Datetime.now()
            })
        
        # 先执行关联订单更新状态，再判断还款订单状态
        repay_order.update_repay_status(fields.Datetime.now())

        # 展期资金流水转正常资金流水
        for i in self.env['platform.flow'].search([('order_id', '=', self.order_id.id)]):
            if i.trade_type not in ["17", "18", "19", "20"]:
                continue
            if i.trade_type == "17":
                i.write({"trade_type": "7"})
            elif i.trade_type == "19":
                i.write({"trade_type": "10"})
            elif i.trade_type == "20":
                i.write({"trade_type": "11"})
            elif i.trade_type == "24":
                i.write({"trade_type": "23"})
    
    def update_extension_status(self, op_time):
        """
        展期成功(展期费支付完成)
        1. 关联财务订单状态改为还款完成
        2. 关联财务订单的还款订单状态改为还款完成
        3. 创建新的财务订单
        4. 创建新的财务订单的还款订单
        4. 创建新的贷超订单
        """
        amount = self.extension_amount - self.repayed_amount - self.settle_amount
        # 成功
        if amount <=0:
            self.write({'status': "2", 'success_time': op_time})
            self.order_id.extension_success(self.extension_amount, op_time)
            return True
        self.write({'status': "4"})
        return 
    
    def after_payment(self, trade_record):
        """
        还款成功回调
        """
        if trade_record.trade_status == "3": # 交易失败
            return
        
        now = fields.Datetime.now()
        # 生成还款记录
        self.env['repay.record'].create({
            "extension_record_id": self.id,
            "order_id": self.order_id.id,
            "repay_type": "2",
            "repay_time": now,
            "platform_order_no": trade_record.platform_order_no,
            "merchant_order_no": trade_record.trade_no,
            "payment_setting_id": trade_record.payment_setting_id.id,
            "payment_way_id": self.order_id.payment_way_id.id,
            "amount": trade_record.trade_amount,
            "fee": trade_record.payment_setting_id.calc_fee(trade_record.trade_amount),
            "tax": 0,
            "order_pending_amount": self.order_id.pending_amount
        })
        
        self.update_extension_status(now)

    def get_pay_link(self, device='pc'):
        """
        获取支付链接
        """
        # 创建交易记录
        payment_channel = self.order_id.repayment_setting_id.payment_channel_id
        trade_no = self.env['ir.sequence'].sudo().next_by_code('trade_record_no_seq')
        if payment_channel.enum_code == 2:
            data = {
                'mchId': int(payment_channel.merchant_no),
                'key': payment_channel.merchant_key,
                'mchOrderNo': trade_no,
                'orderAmount': int(self.pending_amount * 100),
                'notifyUrl': payment_channel.call_back_url or "",
                'returnUrl': payment_channel.redirect_url or "",
                'device': device,
                'uid': self.order_id.loan_uid,
                'customerName': self.order_id.loan_user_name,
                'tel': self.order_id.loan_user_phone
            }
            res = pay_utils.coin_pay.create_pay_order(data)
            pay_url = res.get('data', {}).get('payUrl')
            platform_order_no = res.get('data', {}).get('payOrderId')
        else:
            data = {
                'merchantNo': payment_channel.merchant_no,
                'key': payment_channel.merchant_key,
                'orderNo': trade_no,
                'amount': str(self.pending_amount),
                'notifyUrl': payment_channel.call_back_url or "",
                'userName': self.order_id.loan_user_name,
                'timestamp': datetime.datetime.now().astimezone(tz=pytz.timezone( 'Asia/Kolkata' )).strftime('%Y-%m-%d %H:%M:%S'),
            } 
            res = pay_utils.sf_pay.create_pay_order(data)
            pay_url = res.get('url', "")
            platform_order_no = res.get('platformOrderNo', "")

        # 创建交易记录
        trade_data = {
            'order_id': self.order_id.id,
            'payment_setting_id': self.order_id.repayment_setting_id.id,
            'payment_way_id': self.order_id.repayment_way_id.id,
            'trade_amount': self.pending_amount,
            'trade_no': trade_no,
            'trade_status': '1' if res.get('code', 999) == 200 else '3',
            'trade_type': '1',
            'trade_start_time': fields.Datetime.now(),
            'platform_order_no': platform_order_no,
            'trade_data': res,
            'res_model': 'extension.record',
            'res_id': self.id
        }
        self.env['payment.setting.trade.record'].sudo().create(trade_data)

        return pay_url

    def action_show_settle_wizard(self):
        return {
            'name': '平账',
            'type': 'ir.actions.act_window',
            'res_model': "extension.settle.record",
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size(), 
                'default_extension_record_id': self.id,
                'default_extension_amount': self.extension_amount,
                'default_repayed_amount': self.repayed_amount,
                'default_can_settle_amount': round(self.extension_amount - self.repayed_amount - self.settle_amount, 2)
            }
        }

    def test_action_repay(self):
        """
        测试支付展期费用
        flag: 1-全部 0-部分
        """
        now = fields.Datetime.now()
        flag = self.env.context.get('flag', False)
    
        repay_record_data = {
            'order_id': self.order_id.id,
            'extension_record_id': self.id,
            'repay_type': "2",
            'repay_time': now,
            'platform_order_no': f'P{now.timestamp()}',
            'merchant_order_no': f'M{now.timestamp()}',
            'payment_setting_id': self.order_id.repayment_setting_id.id,
            'payment_way_id': self.order_id.repayment_way_id.id,
            'order_pending_amount': self.order_id.pending_amount,
        }
        if flag:
            repay_record_data.update({
                'amount': self.pending_amount,
                'fee': self.order_id.repayment_setting_id.calc_fee(self.pending_amount),
                'tax': 0
            })
        else:
            amount = round(self.pending_amount/3, 2)
            repay_record_data.update({
                'amount': amount,
                'fee': self.order_id.repayment_setting_id.calc_fee(amount),
                'tax': 0
            })
        self.env['repay.record'].create(repay_record_data)

        self.update_extension_status(now)