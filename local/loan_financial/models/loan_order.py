import logging
import time, datetime
from odoo import models, fields, api, exceptions
from . import enums
from ..utils import date_utils, generate_no


_logger = logging.getLogger(__name__)


class LoanOrder(models.Model):
    _description = '订单管理'
    _inherit = ['loan.order']
    _rec_name = 'order_no'

    wait_duration = fields.Char('未处理时长', compute='_compute_wait_duration')
    wait_duration_tip = fields.Boolean('是否高亮提示',compute='_compute_wait_duration')

    payment_setting_id = fields.Many2one('payment.setting', string='放款/退款渠道', related='product_id.payment_setting_id')
    payment_way_id = fields.Many2one('payment.way',string='放款/退款方式', related='product_id.payment_way_id')
    repayment_setting_id = fields.Many2one('payment.setting', string='还款渠道', related='product_id.payment_setting_id')
    repayment_way_id = fields.Many2one('payment.way', string="还款方式", related='product_id.repayment_way_id')

    # 放款
    pay_order_ids = fields.One2many('pay.order', 'order_id', string='放款订单')
    pay_complete_time = fields.Datetime(string='放款成功时间')
    withdraw_time = fields.Datetime(string='取现时间')
    pay_platform_order_no = fields.Char(string='放款序列号')

    repay_complete_time = fields.Datetime('还款完成时间')
    repay_date = fields.Date('应还日期', compute='_compute_repay_date')
    overdue_days = fields.Integer('逾期天数')
    is_overdue = fields.Boolean('是否逾期')
    overdue_rate = fields.Float('逾期罚息费率', related='product_id.penalty_interest_rate')
    overdue_fee = fields.Float('罚息', compute='_compute_overdue_fee')
    late_fee = fields.Float('滞纳金', compute='_compute_late_fee')
    repay_amount = fields.Float('应还本息', compute='_compute_repay_amount')

    correction_amount = fields.Float('冲正金额', compute='_compute_correction_amount')
    pending_amount = fields.Float('挂账金额', compute="_compute_pending_amount") # 待还金额

    # unpaid_principal = fields.Float('未还本金', compute='_compute_unpaid_amount')
    unpaid_contract_amount = fields.Float('未还合同金额', compute='_compute_unpaid_contract_amount')
    unpaid_overdue_fee = fields.Float('未还罚息', compute='_compute_unpaid_overdue_fee')
    unpaid_late_fee = fields.Float('未还滞纳金', compute='_compute_unpaid_late_fee')

    # 还款数据
    repay_order_ids = fields.One2many('repay.order', 'order_id', '还款订单')
    repay_record_ids = fields.One2many('repay.record', 'order_id', '还款记录')
    repayed_amount = fields.Float('已还款金额', compute='_compute_repayed_amount')
    repayd_principal = fields.Float('已还本金', compute='_compute_repayed_amount')
    repayed_overdue_fee = fields.Float('已还罚息', compute='_compute_repayed_amount')
    repayed_late_fee = fields.Float('已还滞纳金', compute='_compute_repayed_amount')
    platform_profit = fields.Float('平台额外收益', compute='_compute_platform_profit')
    platform_profit_amount = fields.Float('平台利润金额', compute='_compute_platform_profit_amount', store=True)
    
    repay_platform_order_no = fields.Char(string='还款序列号', compute='_compute_repayed_amount')

    # 补单记录 
    additional_record_ids = fields.One2many('additional.record', 'order_id', '补单记录')

    # 减免
    derate_record_ids = fields.One2many('derate.record', 'order_id', '减免记录')
    derate_amount = fields.Float('已减免金额', compute='_compute_derate_amount')
    can_derate_amount = fields.Float('可减免金额', compute='_compute_can_derate_amount')

    # 平账
    settle_record_ids = fields.One2many('settle.record', 'order_id', '平账记录')
    settle_amount = fields.Float('平账金额', digits=(16, 2), compute='_compute_settle_amount')
    settle_principal = fields.Float('平账本金', compute='_compute_settle_amount')
    settle_overdue_fee = fields.Float('平账罚息', compute='_compute_settle_amount')
    settle_late_fee = fields.Float('平账滞纳金', compute='_compute_settle_amount')

    # 退款
    refund_record_ids = fields.One2many('refund.record', 'order_id', '退款记录')
    refund_amount = fields.Float('退款金额', compute='_compute_refund_amount')

    # 展期订单
    is_extension = fields.Boolean(string='是否展期', default=False)
    extend_success_time = fields.Datetime('展期成功时间')
    extend_pay_amount = fields.Float('展期金额', digits=(16, 2))
    extension_order_id = fields.Many2one('loan.order', '展期订单')

    @api.depends('apply_time', 'order_status')
    def _compute_wait_duration(self):
        now = int(time.time())
        for order in self:
            if order.order_status == "3":
                start = order.apply_time
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

    @api.depends('order_status', 'pay_complete_time', 'is_extension')
    def _compute_repay_date(self):
        """
        应还日期计算规则：
        1、如果订单未放款成功(未放款/放款拒绝），应还日期以“申请日期”（含）开始，推算出“借款期限（配置）”天数后的具体日期；即当前日期+6天的具体日期；
        2、如果订单放款成功(放款接口回调结果为“成功”），应还日期以“放款成功时间”日期（含）开始，推算出“借款期限（风控回调）”天数后的具体日期；
        3、展期成功生成的新订单的应还日期是以“展期成功时间”日期(含）开始，推算出原订单“借款期限（风控回调）”天数后的具体日期。
        """
        for order in self:
            if order.order_status == "7":
                start_time = order.pay_complete_time
            elif order.is_extension:
                start_time = order.extend_success_time
            else:
                start_time = order.apply_time
            order.repay_date = (start_time + datetime.timedelta(days=order.loan_period-1)).date()

    @api.depends('overdue_days')
    def _compute_overdue_fee(self):
        """
        罚息=合同金额*罚息利率*逾期天数
        """
        for order in self:
            if not order.overdue_days:
                order.overdue_fee = 0
            else:
                order.overdue_fee = round(order.contract_amount * order.overdue_rate * order.overdue_days, 2)

    @api.depends('is_overdue')
    def _compute_late_fee(self):
        """
        滞纳金 
        """
        for order in self:
            if order.is_overdue:
                order.late_fee = order.product_id.overdue_fine
            else:
                order.late_fee = 0

    @api.depends('overdue_fee', 'late_fee')
    def _compute_repay_amount(self):
        """
        应还金额 = 合同金额+罚息+滞纳金
        """
        for order in self:
            order.repay_amount = round(order.contract_amount + order.overdue_fee + order.late_fee, 2)

    @api.depends('contract_amount', 'repayd_principal', 'settle_principal')
    def _compute_unpaid_contract_amount(self):
        """
        待还合同金额
        """
        for order in self:
            order.unpaid_contract_amount = round(order.contract_amount - order.repayd_principal - order.settle_principal, 2)

    @api.depends('overdue_fee', 'settle_overdue_fee', 'repayed_overdue_fee')
    def _compute_unpaid_overdue_fee(self):
        """
        待还罚息 = 应还罚息-已还罚息-已平账罚息
        """
        for order in self:
            order.unpaid_overdue_fee = round(order.overdue_fee - order.repayed_overdue_fee - order.settle_overdue_fee, 2)

    @api.depends('late_fee', 'repayed_late_fee', 'settle_late_fee')
    def _compute_unpaid_late_fee(self):
        """
        待还滞纳金 = 应还滞纳金-已还滞纳金-已平账滞纳金
        """
        for order in self:
            order.unpaid_late_fee = round(order.late_fee - order.repayed_late_fee - order.settle_late_fee, 2)

    @api.depends('repay_record_ids.is_cancel', 'repay_record_ids.repay_type')
    def _compute_repayed_amount(self):
        for order in self:
            records = order.repay_record_ids.filtered(lambda r: r.repay_type=="1" and not r.is_cancel)
            order.repayed_amount = round(sum([i.amount for i in records]), 2)
            order.repayd_principal = round(sum([i.principal for i in records]), 2)
            order.repayed_overdue_fee = round(sum([i.overdue_fee for i in records]), 2)
            order.repayed_late_fee = round(sum([i.late_fee for i in records]), 2)
            order.repay_platform_order_no = records[0].platform_order_no if records else ''

    @api.depends('repay_amount', 'loan_amount', 'derate_amount', 'pending_amount')
    def _compute_can_derate_amount(self):
        for i in self:
            max_derate_amount = i.repay_amount-i.loan_amount
            can_derate_amount = round(max_derate_amount - i.derate_amount, 2)

            if i.pending_amount <= can_derate_amount:
                derate_amount = i.pending_amount
            else:
                derate_amount = can_derate_amount

            i.can_derate_amount = derate_amount if derate_amount > 0 else 0
        
    @api.depends('derate_amount', 'settle_amount', 'refund_amount')
    def _compute_correction_amount(self):
        """
        冲正金额 =减免金额+平账金额-退款金额
        """
        for order in self:
            order.correction_amount = round(order.derate_amount + order.settle_amount - order.refund_amount, 2)

    @api.depends('repay_amount', 'repayed_amount', 'correction_amount', 'is_extension')
    def _compute_pending_amount(self):
        """
        挂账金额=应还金额-实还金额-减免金额-还款平账金额+退款金额, 挂账金额<0时,计为0
        挂账金额=应还金额-实还金额-冲正金额, 挂账金额<0时,计为0
        """
        for order in self:
            if order.is_extension:
                order.pending_amount = 0
            else:
                pending_amount = round(order.repay_amount - order.repayed_amount - order.correction_amount, 2)
                order.pending_amount = pending_amount if pending_amount > 0 else 0

    @api.depends('repay_amount', 'repayed_amount', 'derate_amount', 'settle_amount', 'refund_amount')
    def _compute_platform_profit(self):
        """
        平台额外收益=（实还金额-取消还款金额）-（合同金额+应还罚息+应还滞纳金）+（减免金额-减免金额退回）+还款平账金额-退款金额, 收益<0时, 计为0
        """
        for order in self:
            platform_profit = round(order.repayed_amount-order.repay_amount+order.derate_amount+order.settle_amount-order.refund_amount, 2)
            order.platform_profit = platform_profit if platform_profit > 0 else 0

    @api.depends('platform_profit')
    def _compute_platform_profit_amount(self):
        for rec in self:
            rec.platform_profit_amount = rec.platform_profit
    
    @api.depends('derate_record_ids.is_effective')
    def _compute_derate_amount(self):
        """
        减免金额 = 未取消的减免记录减免金额之和
        """
        for order in self:
            order.derate_amount = round(sum([record.derate_amount for record in order.derate_record_ids if record.is_effective]), 2)

    @api.depends('settle_record_ids')
    def _compute_settle_amount(self):
        """
        还款平账金额 = 平账记录平账金额之和
        """
        for order in self:
            order.settle_amount = round(sum([record.settle_amount for record in order.settle_record_ids]), 2)
            order.settle_principal = round(sum([record.settle_contract_amount for record in order.settle_record_ids]), 2)
            order.settle_overdue_fee = round(sum([record.settle_overdue_amount for record in order.settle_record_ids]), 2)
            order.settle_late_fee = round(sum([record.settle_late_fee for record in order.settle_record_ids]), 2)

    @api.depends('refund_record_ids.status')
    def _compute_refund_amount(self):
        """
        退款金额 = 退款记录退款金额之和
        """
        for order in self:
            order.refund_amount = round(sum([record.refund_amount for record in order.refund_record_ids if record.status=="3"]), 2)

    @api.model
    def task_compute_overdue(self):
        """
        计算订单是否已经逾期
        """
        now = datetime.date.today()
        for order in self.search([('order_status', '=', '7')]):
            if now > order.repay_date:
                order.overdue_days = (now - order.repay_date).days
                order.is_overdue = True
            else:
                order.overdue_days = 0
                order.is_overdue = False

            if order.repay_date == now:
                order.update_bill_user_status()

            if not order.is_overdue:
                continue

            order.update_bill_order({
                "overdue_flag": True,
                "pending_amount": order.pending_amount,
                "late_fee": order.late_fee
            })

    def _search_platform_profit(self, operator, value):
        if value:
            domain = [('is_overdue', '=', True)]
        else:
            domain = [('is_overdue', '=', False )]
        return domain

    def update_bill_user_status(self, update_fields=["product_earliest_due_time", "fst_time_send_out", "did_repay_flag"]):
        """
        T_derive_user_profile
        did_repay_flag 复贷标识
        product_earliest_due_time 最早到期时间
        fst_time_send_out 首次放款时间
        """
        user_profile = self.env['derive.user.profile'].search([('user_id', '=', self.loan_uid)], limit=1)
        if not user_profile: return

        data = {}
        if "did_repay_flag" in update_fields and not user_profile.did_repay_flag:
            data['did_repay_flag'] = True
        if "product_earliest_due_time" in update_fields and  not user_profile.product_earliest_due_time:
            data['product_earliest_due_time'] = int((self.pay_complete_time+datetime.timedelta(days=self.loan_period-1)).timestamp())
        if "fst_time_send_out" in update_fields and not user_profile.fst_time_send_out:
            data['fst_time_send_out'] = int(self.pay_complete_time.timestamp())
        if data:
            self.update_user_profile(data)
        
    def update_order_status(self, op_time):
        """
        更新订单状态
        """
        self = self.browse(self.id)
        if not self.pending_amount:
            self.write({
                'order_status': '8',
                'repay_complete_time': op_time
            })
            # 更新贷超订单
            bill_data = {
                "bill_status": 4,
                "pending_amount": 0,
                "repay_completion_time": int(op_time.timestamp()),
                "repayed_amount": self.repayed_amount,
                "overdue_flag": False
            }
            if self.is_extension:
                bill_data['extension_bill_id'] = self.extension_order_id.bill_id
            self.update_bill_order(bill_data)
            # 更新贷超用户
            self.update_bill_user_status()
        else:
            self.write({
                'order_status': '7',
                'repay_complete_time': None
            })
            self.update_bill_order({
                "bill_status": 2,
                "pending_amount": self.pending_amount,
                "repay_completion_time": 0,
                "repayed_amount": self.repayed_amount
            })
    
    def get_pay_order(self):
        """
        获取关联的放款订单
        """
        pay_order = self.env['pay.order'].search([('order_id', '=', self.id)], limit=1)
        return pay_order
    
    def get_repay_order(self):
        """
        获取关联的还款订单
        """
        repay_order = self.env['repay.order'].search([('order_id', '=', self.id)], limit=1)
        return repay_order
    
    def create_new_order(self, extension_amount, extension_success_time):
        """
        根据当前订单创建新的财务订单
        1. 创建新的财务订单
        2. 创建新的财务订单的还款订单
        3. 创建新的贷超订单
        """
        order_no = generate_no.generate_order_no("02")
        # 新的贷超订单
        old_bill = self.env['loan.bill'].browse(self.bill_id)
        bill_data = {
            field: getattr(old_bill, field)
            for field in old_bill._fields
            if field not in ['id', 'create_date', 'create_uid', 'write_date', 'write_uid', 'display_name', 'active', 'apply_time', "company_id"]
        }
        timestamp = int(extension_success_time.timestamp())
        bill_data.update({
            "order_no": order_no,
            "bill_status": "2",
            "company_id": old_bill.company_id.id,
            "app_id": old_bill.app_id.id,
            "user_id": old_bill.user_id.id,
            "product_id": old_bill.product_id.id,
            "matrix_id": old_bill.matrix_id,
            "overdue_flag": False,
            "apply_time": timestamp,
            "loan_finish_time": timestamp,
            "due_time": int((extension_success_time + datetime.timedelta(days=self.loan_period-1)).timestamp()),
            "pending_amount": self.contract_amount
        })
        
        new_bill_id = self.create_bill_order(bill_data)
        if not new_bill_id:
            new_bill = self.env['loan.bill'].create(bill_data)
            new_bill_id = new_bill.id

        # 新的财务订单
        amount1 = round(extension_amount/5, 2)
        order_data = {
            'loan_user_id': self.loan_uid, 
            'loan_user_name': self.loan_user_name, 
            'bill_id': new_bill_id, 
            'matrix_id': self.matrix_id, 
            'app_id': self.app_id.id, 
            'app_version': self.app_version, 
            'product_id': self.product_id.id, 
            'order_type': self.order_type, 
            'apply_time': extension_success_time,
            'order_no': order_no,
            'contract_amount': self.contract_amount,
            'loan_period': self.loan_period, 
            'management_fee_rate': self.management_fee_rate, 
            'management_fee': self.management_fee, 
            'loan_amount': 0,
            'bank_name': self.bank_name, 
            'bank_account_no': self.bank_account_no, 
            'bank_ifsc_code': self.bank_ifsc_code, 
            'order_status': '7', 
            'pay_complete_time': extension_success_time,
            'pay_order_ids': [(0, 0, {
                "pay_type": "2",
                "pay_status": "3",
                "is_auto": True,
                "pay_complete_time": extension_success_time,
                "pay_fee": 0,
                "pay_tax": 0,
                "management_fee": extension_amount,
                "pay_interest": amount1,
                "account_management_fee": amount1,
                "platform_service_fee": amount1,
                "risk_fee": amount1,
                "credit_fee": amount1,
            })],
            'repay_order_ids': [(0,0, {
                "repay_type": "1",
                "repay_status": "1"
            })]
        }
        new_order = self.create(order_data)
        return new_order

    def extension_success(self, extension_amount, extension_success_time ):
        """
        展期成功
        1. 财务订单状态改为还款完成
        2. 财务订单的还款订单状态改为还款完成
        3. 贷超订单状态改为还款完成
        4. 创建新的财务订单
        5. 创建新的财务订单的还款订单
        6. 创建新的贷超订单
        """
        # 创建新的财务订单
        new_order = self.create_new_order(extension_amount, extension_success_time)
        
        self.write({
            'is_extension': True, 
            'extend_success_time': extension_success_time,
            'extend_pay_amount': extension_amount,
            'extension_order_id': new_order.id,
        })
        
        self.update_order_status(extension_success_time)
        repay_order = self.get_repay_order()
        repay_order.write({
            "repay_status": "2",
            "repay_type": "2",
            "repay_time":extension_success_time
        })
        
    def action_show_pay_status_1_list(self):

        context = {
            'is_auto_pay': self.env["loan.order.settings"].get_param('is_auto_pay', False)
        }
        return {
            "name": '待放款订单',
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "tree",
            'view_id': self.env.ref('loan_financial.list_pay_order_s1').id,
            "domain": [('order_status', '=', '3')],
            "context": context,
            "target": "main",
            "search_view_id": self.env.ref('loan_financial.search_pay_order_s1').id,
        }
    
    def action_update_order_settings(self):
        """
        财务订单配置
        """
        settings = self.env["loan.order.settings"]
        is_auto_pay = settings.get_param('is_auto_pay', False)
        is_auto_pay = not is_auto_pay
        settings.set_param('is_auto_pay', is_auto_pay)

        # 处理当前未审核的订单
        if is_auto_pay:
            for order in self.search([('order_status', '=', '3')]):
                self.env['pay.order'].approval_pass(order, "自动放款", is_auto=True)

        return self.action_show_pay_status_1_list()
        
    def action_show_pay_order_wizard(self):
        """
        待放款订单-财务审核
        """
        if self.env.context.get('batch_approve_flag'):
            return {
                'name': '批量审核' if self.env.user.lang == "zh_CN" else "Batch Review",
                'type': 'ir.actions.act_window',
                'res_model': "pay.order.batch.approval.wizard",
                'view_mode': 'form',
                'view_id': self.env.ref('loan_financial.wizard_order_batch_approval').id,
                'target': 'new',
                'context': {
                    'dialog_size': self._action_default_size(), 
                    'default_order_ids': ",".join([str(i) for i in self.ids]),
                    'default_approval_result': "2"
                }
            }
        
        approve_flag = self.env.context.get('approve_flag', False)
        
        return {
            'name': '审核通过' if approve_flag else '审核拒绝',
            'type': 'ir.actions.act_window',
            'res_model': "pay.order.approval.wizard",
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.wizard_order_approval').id,
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size(), 
                'default_order_id': self.id,
                'default_approval_result': "2" if approve_flag else "3",
                'default_amount_desc': f"{self.loan_amount}, 是否确定审核{'通过' if approve_flag else '拒绝'}?",
                'default_remark': "无异常通过" if approve_flag else ""
            }
        }
    
    def action_show_additional_record(self):
        """
        显示补单记录
        """
        repay_order = self.get_repay_order()
        return {
            'name': '补单记录' if self.env.user.lang == "zh_CN" else "Reorder Record",
            'type': 'ir.actions.act_window',
            'res_model': "repay.order",
            'res_id': repay_order.id,
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.form_order_additional_record').id,
            'target': 'new',
            'context': {
            }
        }
    
    def action_show_settle_wizard(self):
        """
        创建平账记录
        """
        repay_order = self.get_repay_order()
        return {
            'name': '平账',
            'type': 'ir.actions.act_window',
            'res_model': "settle.record",
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size(), 
                'default_order_id': self.id,
                'default_repay_order_id': repay_order.id,
                'default_order_pending_amount': self.pending_amount,
                'default_order_overdue_fee': self.unpaid_overdue_fee,
                'default_settle_time': fields.Datetime.now()
            }
        }
    
    def action_show_derate_wizard(self):
        """
        创建减免记录
        """
        if self.derate_record_ids.filtered(lambda x: x.fin_approval_status == '1'):
            raise exceptions.UserError('当前订单存在待审核的金额减免申请，审核完成后才可重新申请！')

        return {
            'name': '金额减免申请',
            'type': 'ir.actions.act_window',
            'res_model': "derate.record",
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size(), 
                'default_order_id': self.id,
                "default_order_pending_amount": self.pending_amount,
                'default_max_derate_amount': self.can_derate_amount,
                'default_derate_type': "2",
                'default_fin_approval_status': "1",
            }
        }

    def action_show_refund_wizard(self):
        """
        新建订单退款向导
        """
        refund_type = self.env.context.get('refund_type', '1')
        if refund_type == '1':
            return {
                'name': '退款',
                'type': 'ir.actions.act_window',
                'res_model': "refund.record",
                'view_mode': 'form',
                'view_id': self.env.ref('loan_financial.form_order_refund_record').id,
                'target': 'new',
                'context': {
                    'dialog_size': self._action_default_size(), 
                    'default_order_id': self.id,
                    'default_loan_uid': self.loan_uid,
                    'default_loan_user_name': self.loan_user_name,
                    'default_loan_user_phone': self.loan_user_phone,
                    'default_refund_type': refund_type,
                    'default_status': "2",
                    'default_bank_name': self.bank_name,
                    'default_bank_account_no': self.bank_account_no,
                    'default_bank_ifsc_code': self.bank_ifsc_code,
                    'default_platform_profit': self.platform_profit,
                    "default_payment_setting_id": self.payment_setting_id.id,
                    "default_payment_way_id": self.payment_way_id.id,
                }
            }
        else:
            return {
                'name': '新建退款',
                'type': 'ir.actions.act_window',
                'res_model': "refund.record",
                'view_mode': 'form',
                'view_id': self.env.ref('loan_financial.form_user_refund_record').id,
                'target': 'new',
                'context': {
                    'dialog_size': self._action_default_size(), 
                    'default_refund_type': refund_type,
                    'default_status': "2"
                }
            }

    def _check_order_can_extension(self):
        """
        检查订单是否可以展期
        """
        if self.order_status != '7': # 状态不是待还款，不能展期
            return False
        
        flag = self.product_id.defer_allowed
        if not flag:
            return False
        
        if self.is_overdue:
            return False
        
        if self.pending_amount < self.product_id.defer_min_on_credit_amount:
            return False
        
        now = fields.Datetime.now().date()
        days = (now - self.repay_date).days
        if days < self.product_id.defer_period_from or days > self.product_id.defer_period_to:
            return False
        return True

    def compute_extension_amount(self):
        """
        计算展期金额
        """
        extension_amount = 0
        defer_total_amount_type = self.product_id.defer_total_amount_type
        if defer_total_amount_type == "1": # 合同金额
            total_amount = self.contract_amount
        else: # 挂账金额
            total_amount = self.pending_amount
        
        extension_amount = round(total_amount * self.product_id.defer_interest_rate)
        return extension_amount
    
    def action_show_extension_wizard(self):
        """
        新建展期向导
        """
        if not self._check_order_can_extension():
            raise exceptions.UserError("该订单不符合展期条件，无法申请展期！")
        
        extension_amount = self.compute_extension_amount()
        return {
            'name': '展期申请',
            'type': 'ir.actions.act_window',
            'res_model': "extension.record",
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size(), 
                'default_order_id': self.id,
                'default_extension_days': self.loan_period,
                'default_extension_amount': extension_amount,
                'default_status': "1",
                'default_order_repay_date': self.repay_date,

            }
        }
    
    def action_show_voucher(self):
        pay_order = self.get_pay_order()
        return pay_order.action_show_voucher()

        

class LoanOrderSubBasic(models.AbstractModel):
    _name = 'loan.order.sub.basic'
    _description = '订单子表基础字段'
    _rec_name = 'order_no'

    order_id = fields.Many2one('loan.order', string='订单', required=True, auto_join=True, index=True)
    order_no = fields.Char(string='订单编号', related='order_id.order_no')
    order_user_id = fields.Integer('UserID', related='order_id.loan_uid')
    order_user_name = fields.Char(string='姓名', related='order_id.loan_user_name')
    order_user_phone = fields.Char(string='手机号码', related="order_id.loan_user_phone")
    order_type = fields.Selection(string='订单类型', related='order_id.order_type')
    order_apply_time = fields.Datetime('申请时间', related='order_id.apply_time')
    order_contract_amount = fields.Float(string='合同金额', related='order_id.contract_amount')
    order_loan_period = fields.Integer(string='借款期限', related='order_id.loan_period')
    order_loan_amount = fields.Float(string='放款金额', related='order_id.loan_amount')
    order_management_fee = fields.Float(string='管理费', related='order_id.management_fee')
    order_bank_name = fields.Char(string='收款银行', related="order_id.bank_name")
    order_bank_account_no = fields.Char(string='收款账号', related="order_id.bank_account_no")
    order_bank_ifsc_code = fields.Char(string='银行联行号', related="order_id.bank_ifsc_code")
    order_extend_pay_amount = fields.Float(string='展期应付金额', related='order_id.extend_pay_amount')

    product_id = fields.Many2one('loan.product', string='产品名称', related='order_id.product_id')
    
