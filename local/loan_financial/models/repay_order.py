import logging
import datetime
from odoo import models, fields, api
from . import enums
from ..utils import date_utils


_logger = logging.getLogger(__name__)


class RepayOrder(models.Model):
    _name = 'repay.order'
    _description = '还款订单'
    _inherit = ['loan.basic.model', 'loan.order.sub.basic']
    _table = 'F_repay_order'
    _order = 'repay_time desc'

    pay_complete_time = fields.Datetime(string='放款成功时间', related="order_id.pay_complete_time")
    withdraw_time = fields.Datetime(string='取现时间', related="order_id.withdraw_time")

    repay_type = fields.Selection(selection=enums.REPAY_ORDER_TYPE, string='还款类型')
    repay_status = fields.Selection(selection=enums.REPAY_STATUS, default='0', string='还款状态', index=True)
    repay_time = fields.Datetime(string='还款成功时间')

    # 正常还款数据
    repay_date = fields.Date('应还时间', related="order_id.repay_date")
    overdue_days = fields.Integer('逾期天数', related="order_id.overdue_days")
    is_overdue = fields.Boolean('是否逾期', compute="_compute_is_overdue", inverse='_set_is_overdue', search="_search_is_overdue")
    overdue_fee = fields.Float('罚息', related="order_id.overdue_fee")
    late_fee = fields.Float('滞纳金', related="order_id.late_fee")
    repay_amount = fields.Float('应还本息', related="order_id.repay_amount")
    correction_amount = fields.Float('冲正金额', related="order_id.correction_amount")
    pending_amount = fields.Float('挂账金额', related="order_id.pending_amount") # 待还金额

    order_settle_amount = fields.Float(string='平账金额', related='order_id.settle_amount')
    order_unpaid_contract_amount = fields.Float(string='未还合同金额', related='order_id.unpaid_contract_amount')
    order_unpaid_overdue_fee = fields.Float(string='未还罚息', related='order_id.unpaid_overdue_fee')
    order_unpaid_late_fee = fields.Float(string='未还滞纳金', related='order_id.unpaid_late_fee')
    platform_profit = fields.Float('平台额外收益', related="order_id.platform_profit")

    # 已还数据
    repay_record_ids = fields.One2many('repay.record', 'repay_order_id', '还款记录')
    repayed_amount = fields.Float('已还款金额', compute='_compute_repayed_amount')
    repayed_fee = fields.Float('还款手续费', compute='_compute_repayed_amount')
    repayed_tax = fields.Float('还款税收', compute='_compute_repayed_amount')
    actual_entry_amount = fields.Float('实际入账金额', compute='_compute_actual_entry_amount')

    repayd_principal = fields.Float('已还本金', compute='_compute_repayed_amount')
    repayed_overdue_fee = fields.Float('已还罚息', compute='_compute_repayed_amount')
    repayd_late_fee = fields.Float('已还滞纳金', compute='_compute_repayed_amount')

    platform_order_no = fields.Char(string='还款序列号')
    merchant_order_no = fields.Char(string='还款支付ID')
    payment_setting_id = fields.Many2one('payment.setting', string='还款渠道')
    payment_way_id = fields.Many2one('payment.way',string='还款方式')

    # 补单
    additional_record_ids = fields.One2many('additional.record', 'repay_order_id', '补单记录')

    @api.depends('repay_record_ids', 'repay_record_ids.is_cancel')
    def _compute_repayed_amount(self):
        """
        已还款金额 = 未取消的还款记录还款金额之和
        """
        for order in self:
            records = order.repay_record_ids.filtered(lambda r: not r.is_cancel)
            order.repayed_amount = round(sum([i.amount for i in records]), 2)
            order.repayed_fee = round(sum([i.fee for i in records]), 2)
            order.repayed_tax = round(sum([i.tax for i in records]), 2)

            order.repayd_principal = round(sum([i.principal for i in records]), 2)
            order.repayed_overdue_fee = round(sum([i.overdue_fee for i in records]), 2)
            order.repayd_late_fee = round(sum([i.late_fee for i in records]), 2)

    @api.depends('repayed_amount', 'repayed_fee', 'repayed_tax')
    def _compute_actual_entry_amount(self):
        """
        实际入账金额 = 已还款金额 - 手续费 - 税费
        """
        for order in self:
            order.actual_entry_amount = round(order.repayed_amount - order.repayed_fee - order.repayed_tax, 2)

    @api.depends('derate_record_ids.is_effective')
    def _compute_derate_amount(self):
        """
        减免金额 = 未取消的减免记录减免金额之和
        """
        for order in self:
            order.derate_amount = round(sum([record.derate_amount for record in order.derate_record_ids if record.is_effective]), 2)
    
    @api.depends("order_id.is_overdue")
    def _compute_is_overdue(self):
        for rec in self:
            rec.is_overdue = rec.order_id.is_overdue

    def _search_is_overdue(self, operator, value):
        if value:
            domain = [('order_id.is_overdue', '=', True)]
        else:
            domain = [('order_id.is_overdue', '=', False )]
        return domain
    
    def _set_is_overdue(self):
        ...

    def update_repay_status(self, op_time):
        """
        正常还款后,更新还款状态
        """
        # 先执行关联订单更新状态，再判断还款订单状态
        self.order_id.update_order_status(op_time)

        if not self.order_id.pending_amount:
            self.write({
                'repay_status': '2',
                'repay_time': op_time
            })
            
        else:
            self.write({
                'repay_status': '1',
                'repay_time': None
            })

    def action_show_additional_record(self):
        """
        显示补单记录
        """
        return {
            'name': '补单记录' if self.env.user.lang == "zh_CN" else "Reorder Record",
            'type': 'ir.actions.act_window',
            'res_model': "repay.order",
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.form_order_additional_record').id,
            'target': 'new',
            'context': {
            }
        }
    
    def action_show_create_additional_record(self):
        """
        创建补单记录
        """
        return {
            'name': '补单记录' if self.env.user.lang == "zh_CN" else "Reorder Record",
            'type': 'ir.actions.act_window',
            'res_model': "additional.record",
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.form_additional_record').id,
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size(), 
                'default_repay_order_id': self.id,
                'default_order_id': self.order_id.id
            }
        }
    
    def action_show_settle_wizard(self):
        return {
            'name': '平账',
            'type': 'ir.actions.act_window',
            'res_model': "settle.record",
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size(), 
                'default_order_id': self.order_id.id,
                'default_repay_order_id': self.id,
                'default_order_pending_amount': self.pending_amount,
                'default_order_overdue_fee': self.order_unpaid_overdue_fee,
                'default_settle_time': fields.Datetime.now()
            }
        }
    
    def test_action_repay(self):
        """
        测试还款
        flag: 1-全部 0-部分
        """
        now = fields.Datetime.now()
        flag = self.env.context.get('flag', False)
    
        repay_record_data = {
            'order_id': self.order_id.id,
            'repay_order_id': self.id,
            'repay_type': self.repay_type,
            'repay_time': now,
            'platform_order_no': f'P{now.timestamp()}',
            'merchant_order_no': f'M{now.timestamp()}',
            'payment_setting_id': self.order_id.repayment_setting_id.id,
            'payment_way_id': self.order_id.repayment_way_id.id,
            'order_pending_amount': self.pending_amount,
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

        self.update_repay_status(now)
    
    def after_payment(self, trade_record):
        """
        还款成功回调
        """
        if trade_record.trade_status == "3": # 交易失败
            return
        
        now = fields.Datetime.now()
        # 生成还款记录
        self.env['repay.record'].create({
            "repay_order_id": self.id,
            "order_id": self.order_id.id,
            "repay_type": "1",
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

        self.update_repay_status(now)


















