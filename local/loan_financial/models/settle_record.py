import logging
from typing import Dict, List
from odoo import models, fields, api, exceptions
from . import enums


_logger = logging.getLogger(__name__)


class OrderSettleRecord(models.Model):
    _name = 'settle.record'
    _description = '平账记录'
    _inherit = ['loan.basic.model']
    _table = 'F_settle_record'
    _order = 'settle_time desc'

    order_id = fields.Many2one('loan.order', string="订单编号", required=True, index=True, auto_join=True)
    repay_order_id = fields.Many2one('repay.order', string="还款订单", required=True, index=True, auto_join=True)
    order_no = fields.Char(string='订单编号', related="order_id.order_no")
    loan_uid = fields.Integer('UserID', related='order_id.loan_uid')
    loan_user_name = fields.Char(string='姓名', related='order_id.loan_user_name')
    loan_user_phone = fields.Char(string='手机号码', related="order_id.loan_user_phone")
    product_id = fields.Many2one('loan.product', string='产品名称', related="order_id.product_id")
    order_apply_time = fields.Datetime(string='申请时间', related="order_id.apply_time")

    order_contract_amount = fields.Float(string='合同金额', related="order_id.contract_amount")
    order_pending_amount = fields.Float(string='挂账金额')
    order_overdue_fee = fields.Float(string='罚息')
    order_late_fee = fields.Float(string='滞纳金')

    settle_type = fields.Selection(selection=enums.SETTLE_TYPE, string='平账类型', compute="_compute_settle_type")
    amount = fields.Float(string='平账金额', digits=(16, 2), default=0)
    overdue_amount = fields.Float(string='抹罚息金额', digits=(16, 2),default=0)
    remark = fields.Char(string='备注')
    settle_time = fields.Datetime('平账时间')

    settle_amount = fields.Float(string='平账金额', default=0)
    settle_contract_amount = fields.Float(string='平账合同金额', default=0)
    settle_overdue_amount = fields.Float(string='平账罚息', default=0)
    settle_late_fee = fields.Float(string='平账滞纳金', default=0)
    settle_user_id = fields.Many2one('res.users', string='操作人', default=lambda self: self.env.user)

    @api.depends('amount', "overdue_amount")
    def _compute_settle_type(self):
        """
        平账：只要填写了“平账金额”的平账记录；
        抹罚息：仅填写了“抹罚息金额”，没有填写“平账金额”的平账记录
        """
        for record in self:
            if record.amount:
                record.settle_type = '1'
            else:
                record.settle_type = '2'

    @api.model
    def compute_settle_amount(self, data):
        """
        平账金额≤待还合同金额，则平账合同金额=平账金额，平账罚息=0,平账滞纳金=0
        """
        loan_order = self.env['loan.order'].browse(data['order_id'])
        a = loan_order.unpaid_contract_amount
        b = loan_order.unpaid_overdue_fee

        amount = data.get('amount', 0)
        overdue_amount = data.get('overdue_amount', 0)

        if overdue_amount:
            data["settle_overdue_amount"] = overdue_amount
        
        if amount <= a:
            data["settle_contract_amount"] = amount
            
        elif amount + overdue_amount <= a + b:
            data.update({
                "settle_contract_amount": a,
                "settle_overdue_amount": round(amount + overdue_amount - a, 2)
            })
        else:
            data.update({
                "settle_contract_amount": a,
                "settle_overdue_amount": b,
                "settle_late_fee": round(amount + overdue_amount - a - b, 2)
            })
        data["settle_amount"] = round(amount + overdue_amount, 2)
        return data

    @api.model_create_multi
    def create(self, vals_list):
        invalid_flag, too_large_flag = self.verify_params(params=vals_list)
        if invalid_flag is True:
            raise exceptions.ValidationError('\n\n● 平账金额\n● 抹罚息金额\n\n必须要有一个值:>0')
        if too_large_flag is True:
            raise exceptions.ValidationError('\n\n● 平账金额\n● 抹罚息金额\n\n必须满足:平账金额 + 抹罚息金额 ≤ 挂账金额;抹罚息金额≤待还罚息')
        for i in vals_list:
            self.compute_settle_amount(i)
        objs = super().create(vals_list)
        flow_data = []
        for obj in objs:
            # obj._update_settle_amount()
            obj.repay_order_id.update_repay_status(obj.settle_time)
            flow_data.append({
                "order_id": obj.order_id.id,
                "flow_time": obj.settle_time,
                "flow_type": enums.FLOW_TYPE[0][0],
                "flow_amount": round(obj.amount + obj.overdue_amount, 2),
                "trade_type": enums.TRADE_TYPE[22][0]
            })
        self.env['platform.flow'].create(flow_data)
        return objs

    @staticmethod
    def verify_params(params: list) -> tuple:
        """
        参数校验：
        1. 平账金额 或 抹罚息金额  必须要有一个值大于0
        2. 平账金额 + 抹罚息金额 ≤ 挂账金额。
        """
        invalid_flag = False
        too_large_flag = False
        for param in params:
            order_pending_amount = param.get('order_pending_amount')
            settle_amount = param.get('amount')
            overdue_amount = param.get('overdue_amount')
            if not settle_amount and not overdue_amount:
                invalid_flag = True
                break
            if settle_amount + overdue_amount > order_pending_amount:
                too_large_flag = True
                break
            if overdue_amount > param.get('order_overdue_fee'):
                too_large_flag = True
                break
        return invalid_flag, too_large_flag


class ExtensionSettleRecord(models.Model):
    _name = 'extension.settle.record'
    _description = '展期平账记录'
    _inherit = ['loan.basic.model']
    _table = 'F_extension_settle_record'
    _order = 'settle_time desc'

    extension_record_id = fields.Many2one('extension.record', string="展期记录", index=True, auto_join=True)
    loan_order_id = fields.Many2one('loan.order', string="订单编号", auto_join=True, related="extension_record_id.order_id")
    platform_order_no = fields.Char(string='展期序列号', related="extension_record_id.platform_order_no")

    extension_amount = fields.Float(string='展期应付金额')
    repayed_amount = fields.Float(string='展期实付金额')
    can_settle_amount = fields.Float(string='可平账金额')
    settle_amount = fields.Float(string='平账金额', digits=(16, 2), required=True)
    remark = fields.Char(string='备注', required=True)

    settle_time = fields.Datetime('平账时间', default=fields.Datetime.now)
    settle_user_id = fields.Many2one('res.users', string='操作人', default=lambda self: self.env.user)

    @api.model
    def create(self, vals):
        settle_amount = vals.get('settle_amount')
        if settle_amount <= 0 or settle_amount > vals.get('can_settle_amount'):
            raise exceptions.UserError('0<平账金额≤可平账金额,请调整')
        obj = super().create(vals)
        obj.extension_record_id.update_extension_status(obj.settle_time)
        # 资金流水
        self.env['platform.flow'].create({
            "order_id": obj.loan_order_id.id,
            "flow_time": obj.settle_time,
            "flow_type": enums.FLOW_TYPE[0][0],
            "flow_amount": obj.settle_amount,
            "trade_type": enums.TRADE_TYPE[23][0]
        })
        return obj
        