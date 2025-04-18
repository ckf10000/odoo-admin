import logging
from typing import Dict, List
from odoo import models, fields, api
from . import enums


_logger = logging.getLogger(__name__)


class RepayRecord(models.Model):
    _name = 'repay.record'
    _description = '还款记录'
    _inherit = ['loan.basic.model']
    _table = 'F_repay_record'

    repay_order_id = fields.Many2one('repay.order', auto_join=True, index=True)
    order_id = fields.Many2one('loan.order', index=True)
    order_no = fields.Char(string='订单编号', related="order_id.order_no")
    loan_uid = fields.Integer('UserID', related='order_id.loan_uid')
    loan_user_name = fields.Char(string='姓名', related='order_id.loan_user_name')
    loan_user_phone = fields.Char(string='手机号码', related="order_id.loan_user_phone")
    product_id = fields.Many2one('loan.product', string='产品名称', related="order_id.product_id")
    contract_amount = fields.Float(string='合同金额', related="order_id.contract_amount")
    loan_amount = fields.Float('放款金额', related="order_id.loan_amount")
    loan_period = fields.Integer(string='借款期限', related="order_id.loan_period")
    repay_amount = fields.Float('应还本息', related="order_id.repay_amount")
    repay_date = fields.Date('应还时间', related="order_id.repay_date")
    overdue_days = fields.Integer('逾期天数', related="order_id.overdue_days")
    correction_amount = fields.Float('冲正金额', related="order_id.correction_amount")
    pay_time = fields.Datetime(string='放款成功时间', related="order_id.pay_complete_time")
    order_overdue_fee = fields.Float('罚息', related="order_id.overdue_fee")
    order_late_fee = fields.Float('滞纳金', related="order_id.late_fee")

    # 支付数据
    repay_type = fields.Selection(enums.REPAY_RECORD_TYPE, string='收款类型')
    repay_time = fields.Datetime(string='支付成功时间')
    platform_order_no = fields.Char(string='还款序列号')
    merchant_order_no = fields.Char(string='还款支付ID')
    payment_setting_id = fields.Many2one('payment.setting', string='还款渠道')
    payment_way_id = fields.Many2one('payment.way',string='还款方式')
    
    amount = fields.Float(string='支付金额', digits=(16, 2), default=0)
    fee = fields.Float(string='支付手续费', digits=(16, 2), default=0)
    tax = fields.Float(string='支付税收', digits=(16, 2), default=0)
    actual_repay_amount = fields.Float(string='实际入账金额', compute="_compute_actual_repay_amount", store=True)
    # 正常还款数据
    principal = fields.Float(string='本金还款', digits=(16, 2), default=0)
    overdue_fee = fields.Float('罚息还款', digits=(16, 2), default=0)
    late_fee = fields.Float('滞纳金还款', digits=(16, 2), default=0)
    platform_profit = fields.Float('平台额外收益', digits=(16, 2), default=0)
    order_pending_amount = fields.Float('原挂账金额', digits=(16, 2), default=0)
    write_off_amount = fields.Float(string='销账金额', compute="_compute_write_off_amount")
    pending_amount = fields.Float('剩余挂账金额', compute="_compute_write_off_amount")

    is_cancel = fields.Boolean(string='是否取消', default=False)
    cancel_time = fields.Datetime(string='取消时间')
    cancel_user_id = fields.Many2one('res.users', string='操作人')
    cancel_remark = fields.Text(string='取消备注')

    extension_record_id = fields.Many2one('extension.record', string='展期记录')

    @api.depends('amount', 'fee', 'tax')
    def _compute_actual_repay_amount(self):
        """
        实际入账金额=支付金额-支付手续费-支付税收（增值税）
        """
        for record in self:
            record.actual_repay_amount = round(record.amount - record.fee - record.tax, 2)

    @api.depends('repay_type', 'amount', 'order_pending_amount')
    def _compute_write_off_amount(self):
        """
        如果收款类型是“正常收款”，则当支付金额＞原挂账金额，销账金额=原挂账金额；当支付金额≤原挂账金额，则销账金额=支付金额；如果收款类型为“展期收款”，则销账金额=0
        """
        for record in self:
            if record.repay_type == '1':
                record.write_off_amount = record.amount if record.amount <= record.order_pending_amount else record.order_pending_amount
            else:
                record.write_off_amount = 0
            
            record.pending_amount = round(record.order_pending_amount - record.write_off_amount, 2)

    @api.model
    def _prepare_compute_vals(self, vals):
        """
        a.  如果：支付金额≤待还合同金额，
            则：还款本金=支付金额，还款罚息=0,还款滞纳金=0
        b.  如果：待还合同金额＜支付金额≤待还合同金额+待还罚息，
            则：还款本金=待还合同金额，还款罚息=支付金额-待还合同金额，还款滞纳金=0
        c.  如果：待还合同金额+待还罚息＜支付金额≤待还合同金额+待还罚息+待还滞纳金，
            则：还款本金=待还合同金额，还款罚息=待还罚息，还款滞纳金=支付金额-待还合同金额-待还罚息
        """
        amount = vals.get('amount')
        repay_order = self.env['repay.order'].browse(vals.get('repay_order_id'))

        # 展期收款不用计算
        if vals.get('repay_type') == "2":
            extension_record_id = self.env['extension.record'].browse(vals.get('extension_record_id'))
            if amount > extension_record_id.pending_amount:
                vals['platform_profit'] = round(amount - extension_record_id.pending_amount, 2)
            return vals
        
        order = repay_order.order_id
        if order.order_status == '8':
            order_money = 0
            order_overdue_fee = 0
            order_late_fee = 0
        else:
            order_money = order.unpaid_contract_amount # 待还金额
            order_overdue_fee = order.unpaid_overdue_fee # 待还罚息
            order_late_fee = order.unpaid_late_fee  # 待还滞纳金

        principal, overdue_fee, late_fee, platform_profit = 0,0,0,0
        if amount <= order_money:
            principal = amount
        else:
            if amount <= order_money + order_overdue_fee:
                principal = order_money
                overdue_fee = round(amount - order_money, 2)
            elif amount <= order_money + order_overdue_fee + order_late_fee:
                principal = order_money
                overdue_fee = order_overdue_fee
                late_fee = round(amount - order_money - order_overdue_fee, 2)
            else:
                principal = order_money
                overdue_fee = order_overdue_fee
                late_fee = order_late_fee
                platform_profit = round(amount - order_money - order_overdue_fee - order_late_fee, 2)
        
        vals.update({
            'principal': principal,
            'overdue_fee': overdue_fee,
            'late_fee': late_fee,
            'platform_profit': platform_profit
        })
        return vals
    
    @api.model
    def create(self, vals):
        vals = self._prepare_compute_vals(vals)
        obj =  super().create(vals)
        # 更新还款订单数据
        if obj.repay_order_id:
            obj.repay_order_id.write({
                'platform_order_no': obj.platform_order_no,
                'merchant_order_no': obj.merchant_order_no,
                'payment_setting_id': obj.payment_setting_id.id,
                'payment_way_id': obj.payment_way_id.id
            })
        if obj.extension_record_id:
            obj.extension_record_id.write({
                'platform_order_no': obj.platform_order_no,
                'merchant_order_no': obj.merchant_order_no,
                'payment_setting_id': obj.payment_setting_id.id,
                'payment_way_id': obj.payment_way_id.id
            })
        
        # 创建资金流水
        flow_data = []
        base_data = {
            "order_id": obj.order_id.id,
            "product_id": obj.product_id.id,
            "payment_setting_id": obj.payment_setting_id.id,
            "payment_way_id": obj.payment_way_id.id,
            "flow_time": obj.repay_time,
        }
        if obj.repay_type == "1":
            if obj.principal:
                flow_data.append({
                    "flow_type": enums.FLOW_TYPE[1][0],
                    "flow_amount": obj.principal,
                    "trade_type": enums.TRADE_TYPE[6][0],
                    **base_data
                })
            if obj.overdue_fee:
                flow_data.append({
                    "flow_type": enums.FLOW_TYPE[1][0],
                    "flow_amount": obj.overdue_fee,
                    "trade_type": enums.TRADE_TYPE[7][0],
                    **base_data
                })
            if obj.late_fee:
                flow_data.append({
                    "flow_type": enums.FLOW_TYPE[1][0],
                    "flow_amount": obj.late_fee,
                    "trade_type": enums.TRADE_TYPE[8][0],
                    **base_data
                })
            if obj.fee:
                flow_data.append({
                    "flow_type": enums.FLOW_TYPE[0][0],
                    "flow_amount": obj.fee,
                    "trade_type": enums.TRADE_TYPE[9][0],
                    **base_data
                })
            
            if obj.tax:
                flow_data.append({
                    "flow_type": enums.FLOW_TYPE[0][0],
                    "flow_amount": obj.tax,
                    "trade_type": enums.TRADE_TYPE[10][0],
                    **base_data
                })

            if obj.platform_profit:
                flow_data.append({
                    "flow_type": enums.FLOW_TYPE[1][0],
                    "flow_amount": obj.platform_profit,
                    "trade_type": enums.TRADE_TYPE[11][0],
                    **base_data
                })
        else:
            flow_data = []
            if obj.platform_profit: # 有平台利润，意味着展期费还完了，费用=还款金额-平台利润
                flow_data.append({
                    "flow_type": enums.FLOW_TYPE[1][0],
                    "flow_amount": round(obj.amount - obj.platform_profit, 2),
                    "trade_type": enums.TRADE_TYPE[16][0],
                    **base_data
                })
                flow_data.append({
                    "flow_type": enums.FLOW_TYPE[1][0],
                    "flow_amount": obj.platform_profit,
                    "trade_type": enums.TRADE_TYPE[17][0],
                    **base_data
                })
            else:
                flow_data.append({
                    "flow_type": enums.FLOW_TYPE[1][0],
                    "flow_amount": obj.amount,
                    "trade_type": enums.TRADE_TYPE[16][0],
                    **base_data
                })

            if obj.fee:
                flow_data.append({
                    "flow_type": enums.FLOW_TYPE[0][0],
                    "flow_amount": obj.fee,
                    "trade_type": enums.TRADE_TYPE[18][0],
                    **base_data
                })
            
            if obj.tax:
                flow_data.append({
                    "flow_type": enums.FLOW_TYPE[0][0],
                    "flow_amount": obj.tax,
                    "trade_type": enums.TRADE_TYPE[19][0],
                    **base_data
                })
        self.env['platform.flow'].create(flow_data)
        return obj

    def action_show_cancel_record(self):
        """
        """
        return {
            'name': '取消还款',
            'type': 'ir.actions.act_window',
            'res_model': "repay.record.cancel.wizard",
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size(), 
                'default_repay_record_id': self.id,
                'default_order_no': self.order_no,
                'default_loan_user_name': self.loan_user_name,
                'default_loan_user_phone': self.loan_user_phone,
                'default_pending_amount': self.pending_amount,
                'default_product_id': self.product_id.id,
                'default_contract_amount': self.contract_amount,
                'default_amount': self.amount,
                'default_new_pending_amount': round(self.pending_amount + self.amount, 2)
            }
        }


class RepayRecordCancelWizard(models.TransientModel):
    _name = 'repay.record.cancel.wizard'
    _description = '取消还款向导'

    repay_record_id = fields.Many2one('repay.record', string='还款记录', auto_join=True, required=True)
    order_id = fields.Many2one('loan.order', related="repay_record_id.order_id")
    order_no = fields.Char(string='订单号', readonly=True)
    loan_user_name = fields.Char(string='姓名', readonly=True)
    loan_user_phone = fields.Char(string='手机号码', readonly=True)
    product_id = fields.Many2one('loan.product',  readonly=True)
    contract_amount = fields.Float(string='合同金额', readonly=True)
    pending_amount = fields.Float('挂账金额', readonly=True)

    amount = fields.Float(string='取消还款金额', readonly=True)
    new_pending_amount = fields.Float('取消还款后挂账金额', readonly=True)
    remark = fields.Text('备注')

    @api.model
    def create(self, vals):
        obj = super(RepayRecordCancelWizard, self).create(vals)
        oper_time = fields.Datetime.now()
        obj.repay_record_id.write({
            "is_cancel": True,
            "cancel_time": oper_time,
            "cancel_user_id": self.env.user.id,
            "cancel_remark": obj.remark,
        })

        # 流水
        self.env['platform.flow'].create({
            "order_id": obj.repay_record_id.order_id.id,
            "payment_setting_id": obj.repay_record_id.payment_setting_id.id,
            "payment_way_id": obj.repay_record_id.payment_way_id.id,
            "flow_type": enums.FLOW_TYPE[0][0],
            "flow_amount": obj.amount,
            "trade_type": enums.TRADE_TYPE[12][0],
            "flow_time": oper_time
        })

        obj.repay_record_id.repay_order_id.update_repay_status(oper_time)
        return obj
