import logging
import time, datetime, pytz
from odoo import models, fields, api
from . import enums
from ..utils import date_utils
from ..utils import pay_utils


_logger = logging.getLogger(__name__)


class PayOrder(models.Model):
    _name = 'pay.order'
    _description = '放款订单'
    _inherit = ['loan.basic.model', 'loan.order.sub.basic']
    _table = 'F_pay_order'
    
    pay_type = fields.Selection(selection=enums.PAY_TYPE, string='放款类型')
    is_auto = fields.Boolean(string='是否自动放款', default=False)
    pay_way_display = fields.Char('放款操作', compute="_compute_pay_way_display")
    pay_status = fields.Selection(selection=enums.PAY_STATUS, default='0', string='放款状态', index=True)

    financial_user_id = fields.Many2one('res.users', string='财务员审核人员')
    financial_status = fields.Selection(enums.FINANCIAL_STATUS, default='1', string='财务审核结论', index=True)
    financial_remark = fields.Text(string='财务审核备注')
    financial_time = fields.Datetime(string='财务审核时间') # 放款时间

    pay_amount = fields.Float(string='放款金额', compute='_compute_pay_amount')
    pay_complete_time = fields.Datetime(string='放款成功时间')  # 完成放款时间, 支付接口回调时间
    withdraw_time = fields.Datetime(string='取现时间', compute='_compute_withdraw_time') 
    
    # 放款记录
    pay_record_ids = fields.One2many('pay.record', 'pay_order_id', string='放款记录')
    pay_record_count = fields.Integer(string='放款次数', compute='_compute_pay_records')
    trade_count = fields.Integer(string='放款次数')
    # pay_record_amount = fields.Float(string='放款金额', compute='_compute_from_record_pay_record')
    management_fee = fields.Float(string='管理费(砍头息)')
    pay_fee = fields.Float(string='放款手续费')
    pay_tax = fields.Float(string='放款税收')
    actual_pay_amount = fields.Float(string='实际出账金额', compute='_compute_actual_pay_amount', store=True)

    pay_interest = fields.Float(string='利息', digits=(16, 2), default=0.0)
    account_management_fee = fields.Float(string='账户管理费', digits=(16, 2), default=0.0)
    platform_service_fee = fields.Float(string='平台服务费', digits=(16, 2), default=0.0)
    risk_fee = fields.Float(string='风险费', digits=(16, 2), default=0.0)
    credit_fee = fields.Float(string='信用费', digits=(16, 2), default=0.0)

    payment_setting_id = fields.Many2one('payment.setting', string='放款渠道')
    payment_way_id = fields.Many2one('payment.way',string='放款方式')
    platform_order_no = fields.Char(string='放款序列号')
    merchant_order_no = fields.Char(string='放款支付ID')
    fail_reason = fields.Char(string='放款失败原因')

    refuse_reason = fields.Char(string='拒绝原因')
    refuse_time = fields.Datetime(string='拒绝时间')

    # 其他
    pay_voucher = fields.Char(string='放款凭证描述', compute='_compute_payment_voucher')
    modify_account_status = fields.Selection(selection=enums.MODIFY_ACCOUNT_STATUS, default='0', string='修改账户状态')

    wait_duration = fields.Char('已处理时长', compute='_compute_wait_duration')
    wait_duration_tip = fields.Boolean('是否高亮提示',compute='_compute_wait_duration')

    @api.depends('is_auto')
    def _compute_pay_way_display(self):
        for rec in self:
            rec.pay_way_display ='手动放款' if not rec.is_auto else '自动放款'

    @api.depends("pay_type", "order_loan_amount")
    def _compute_pay_amount(self):
        """
        a. 如果放款类型为“正常放款”：放款金额=合同金额-管理费用=合同金额-合同金额*当前订单所属产品的管理费利率（以风控接口回调的“管理费利率”为准）;
        b. 如果放款类型为“展期放款”：放款金额=0
        """
        for rec in self:
            rec.pay_amount = rec.order_loan_amount if rec.pay_type == '1' else 0
        
    @api.depends("pay_type", "pay_complete_time")
    def _compute_withdraw_time(self):
        """
        如果放款类型为“正常放款”，则：取现时间=放款成功时间；如果放款类型为“展期放款”，则：取现时间显示为“-”；
        """
        for order in self:
            order.withdraw_time = order.pay_complete_time if order.pay_type == "1" else None
    
    @api.depends("pay_type")
    def _compute_management_fee(self):
        """
        a. 如果放款类型为“正常放款”：管理费用（砍头息）=合同金额*当前订单所属产品的管理费利率（“管理费利率”在风控/信审通过后由风控接口返回）;
        b. 如果放款类型为“展期放款”：管理费用（砍头息）=原订单“展期应付金额”
        """
        for order in self:
            if order.pay_type == "1":
                order.management_fee = order.order_management_fee
            else:
                order.management_fee = order.order_extend_pay_amount

    @api.depends("pay_record_ids.is_success")
    def _compute_pay_records(self):
        """
        根据放款记录, 汇总放款数据
        """
        for order in self:
            recs = order.pay_record_ids
            order.pay_record_count = len(recs)
            fee, tax = 0, 0
            for r in recs:
                if not r.is_success:
                    continue
                fee += r.fee
                tax += r.tax
            order.pay_fee = round(fee, 2)
            order.pay_tax = round(tax, 2)

    @api.depends("pay_amount", "pay_fee", "pay_tax")
    def _compute_actual_pay_amount(self):
        """
        实际出账金额=放款金额+放款手续费+放款税收
        """
        for order in self:
            order.actual_pay_amount = round(order.pay_amount + order.pay_fee + order.pay_tax, 2)

    @api.depends('create_date', 'pay_status', 'financial_time')
    def _compute_wait_duration(self):
        now = int(time.time())
        for order in self:
            if order.pay_status == "1":
                start = order.create_date
            elif order.pay_status == "2":
                start = order.financial_time
            elif order.pay_status == "4":
                start = order.pay_complete_time
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

    @api.depends()
    def _compute_payment_voucher(self):
        for order in self:
            order.pay_voucher = 'Payment'

    @api.model
    def approval_pass(self, loan_order, remark, is_auto=False):
        """
        审批通过
        """
        now = fields.Datetime.now()
        amount1 = round(loan_order.management_fee/5, 2)
        pay_order_data = {
            "order_id": loan_order.id,
            "pay_type": "1",
            "pay_status": "2",
            "is_auto": is_auto,
            "payment_setting_id": loan_order.payment_setting_id.id,
            "payment_way_id": loan_order.payment_way_id.id,
            "financial_user_id": self.env.user.id if self.env.user else None,
            "financial_status": "2",
            "financial_remark": remark,
            "financial_time": now,
            "management_fee": loan_order.management_fee,
            "pay_interest": amount1,
            "account_management_fee": amount1,
            "platform_service_fee": amount1,
            "risk_fee": amount1,
            "credit_fee": amount1,
            "trade_count": 1
        }
        pay_order = self.create(pay_order_data)
        loan_order.write({
            "order_status": "5",
        })
        pay_order.call_pay_handler()
        return pay_order

    @api.model
    def approval_refuse(self, loan_order, remark):
        """
        审批拒绝
        """
        now = fields.Datetime.now()
        pay_order_data = {
            "order_id": loan_order.id,
            "pay_type": "1",
            "pay_status": "5",
            "payment_setting_id": loan_order.payment_setting_id.id,
            "payment_way_id": loan_order.payment_way_id.id,
            "financial_user_id": self.env.user.id if self.env.user else None,
            "financial_status": "3",
            "financial_remark": remark,
            "financial_time": now,
            "refuse_reason": remark,
            "refuse_time": now
        }
        pay_order = self.create(pay_order_data)
        
        loan_order.write({
            "order_status": "4",
            "refuse_reason": remark,
            "refuse_time": now
        })

        loan_order.update_bill_order({
            "bill_status": 3,
            "refuse_time": int(now.timestamp()),
            "refuse_code": 2
        })
        return pay_order
        
    def action_show_voucher(self):
        """
        成功订单-查看凭证
        """
        return {
            'name': '放款凭证',
            'type': 'ir.actions.act_window',
            'res_model': "pay.order",
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.form_pay_order_voucher').id,
            'res_id': self.id,
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size()
            }
        }
    
    def action_download_voucher(self):
        """
        成功订单-下载凭证
        """
        form_view_id = self.env.ref('loan_financial.form_pay_order_voucher')
        url = f"/download_order_voucher?res_id={self.id}&res_model={self._name}&view_id={form_view_id.id}"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
    
    def action_update_user_name(self):
        """
        失败订单-更新用户姓名
        """
        return {
            'name': '修改姓名',
            'type': 'ir.actions.act_window',
            'res_model': "pay.order.update.wizard",
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size(), 
                'default_order_id': self.id,
                'default_update_type': "1"
            }
        }
    
    def action_payment_again(self):
        """
        失败订单-重新放款
        """
        self.write({
            'pay_status': "2",
            'financial_time': fields.Datetime.now(),
            'trade_count': self.trade_count + 1
        })

        self.order_id.write({
            'order_status': "5"
        })

        self.order_id.update_bill_order({
            'bill_status': "1"
        })

        self.call_pay_handler()
        return 
    
    def action_refuse_payment(self):
        """
        失败订单-拒绝放款
        """
        return {
            'name': '放款拒绝',
            'type': 'ir.actions.act_window',
            'res_model': "pay.order.update.wizard",
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size(), 
                'default_order_id': self.id,
                'default_update_type': "2"
            }
        }
    
    def action_update_bank_account(self):
        """
        失败订单-更新银行账户
        """
        self.write({
            'modify_account_status': '1'
        })
        self.order_id.update_bill_order({
                "bill_status": 5
            })
        return 
    
    def call_pay_handler(self):
        """
        调用放款接口
        """
        if not self.pay_amount:
            return
        now = datetime.datetime.now()
        payment_channel = self.payment_setting_id.payment_channel_id
        trade_no = self.env['ir.sequence'].next_by_code('trade_record_no_seq')
        trade_status = "1"
        fail_reason = ""
        if payment_channel.enum_code == 1:
            params = {
                'merchantNo': payment_channel.merchant_no,
                'key': payment_channel.merchant_key,
                'orderNo': trade_no,  
                'amount': str(self.pay_amount),    
                'notifyUrl': payment_channel.call_back_url,
                'name': self.order_user_name,
                'account': self.order_bank_account_no,
                'ifscCode': self.order_bank_ifsc_code,
                'timestamp': now.astimezone(tz=pytz.timezone( 'Asia/Kolkata' )).strftime('%Y-%m-%d %H:%M:%S'),
            }
            trade_data = pay_utils.sf_pay.create_transfer_order(params)
            if trade_data['code'] != 0:
                trade_status = "3"
                fail_reason = trade_data['code']
            platform_order_no = trade_data.get("platformOrderNo")
        else:
            params = {
                'type': 1,
                'mchId': int(payment_channel.merchant_no),
                'key': payment_channel.merchant_key,
                'productId': 27,
                'mchOrderNo': trade_no,
                'orderAmount': int(self.pay_amount*100),
                # 'orderAmount': 11000,
                'notifyUrl': payment_channel.call_back_url,
                'clientIp': '127.0.0.1',
                'device': 'pc',
                'uid': self.order_user_id,
                'customerName': self.order_user_name,
                'tel': self.order_user_phone,
                # 'tel': '9835814745',
                'email': 'test@gmail.com',
                'returnType': 'json',
                'accountname': self.order_user_name,
                'cardnumber': self.order_bank_account_no,
                'ifsc': self.order_bank_ifsc_code,
                'bankname': 'wavepay',
                # 'accountname': 'Ajay Kumar mandal',
                # 'cardnumber': '5448335547',
                # 'ifsc': 'KKBK0004265',
                'mode': 'IMPS',
                
            } 
            trade_data = pay_utils.coin_pay.create_transfer_order(params)
            if trade_data.get('code', 999) != 200:
                trade_status = "3"
                fail_reason = trade_data['message']
            platform_order_no = trade_data.get('data', {}).get('payOrderId')
            
        # 创建交易记录
        trade_data = {
            'order_id': self.order_id.id,
            'payment_setting_id': self.payment_setting_id.id,
            'payment_way_id': self.payment_way_id.id,
            'trade_amount': self.pay_amount,
            'trade_no': trade_no,
            'trade_status': trade_status,
            'trade_type': '2',
            'trade_start_time': now,
            'platform_order_no': platform_order_no,
            'trade_data': trade_data,
            'res_model': self._name,
            'res_id': self.id
        }
        trade_record = self.env['payment.setting.trade.record'].create(trade_data)

        # 更新订单信息
        if trade_status == "3":
            pay_order_data={
                'pay_status': '4',
                'pay_complete_time': now,
                "fail_reason": fail_reason
            }
            self.write(pay_order_data)
            self.order_id.write({
                "order_status": "6"
            })
        return 
            
    def after_payment(self, trade_record):
        """
        放款完成
        """  
        now = fields.Datetime.now()
        pay_order_data = {
            "platform_order_no": trade_record.platform_order_no,
            "merchant_order_no": trade_record.trade_no,
            "pay_complete_time": now,
        }
        if trade_record.trade_status == "2":
            # 支付状态
            pay_order_data.update({
                "pay_status": "3",
                "pay_complete_time": now,
                "pay_fee": self.payment_setting_id.calc_fee(self.pay_amount)
            })
            self.write(pay_order_data)
            # 财务订单
            self.order_id.write({
                "order_status": "7",
                "pay_complete_time": now,
                "withdraw_time": self.withdraw_time,
                "pay_platform_order_no": trade_record.platform_order_no
            })
            # 贷超订单
            self.order_id.update_bill_order({
                "bill_status": 2,
                "pending_amount": self.order_id.pending_amount,
                "loan_finish_time": int(now.timestamp()),
                "due_time": int((now+datetime.timedelta(days=self.order_id.loan_period-1)).timestamp())
            })
            
            self.order_id.update_bill_user_status(update_fields=["product_earliest_due_time", "fst_time_send_out"])
            
            # 生成待还订单
            repay_order = self.order_id.get_repay_order()
            if not repay_order:
                self.env['repay.order'].create({
                    "order_id": self.order_id.id,
                    "repay_type": "1",
                    "repay_status": "1"
                })

                # 资金流水
                base_data = {
                    "order_id": self.order_id.id,
                    "product_id": self.product_id.id,
                    "payment_setting_id": self.payment_setting_id.id,
                    "payment_way_id": self.payment_way_id.id,
                    "flow_time": now
                }
                flow_data = []
                if self.pay_amount:
                    flow_data.append({
                        "flow_type": enums.FLOW_TYPE[0][0],
                        "flow_amount": self.pay_amount,
                        "trade_type": enums.TRADE_TYPE[0][0],
                        **base_data
                    })
                if self.order_management_fee:
                    flow_data.append({
                        **base_data,
                        "flow_type": enums.FLOW_TYPE[1][0],
                        "flow_amount": self.order_management_fee,
                        "trade_type": enums.TRADE_TYPE[1][0],
                    })
                if self.pay_fee:
                    flow_data.append({
                        **base_data,
                        "flow_type": enums.FLOW_TYPE[0][0],
                        "flow_amount": self.pay_fee,
                        "trade_type": enums.TRADE_TYPE[2][0],
                    })                      
                self.env['platform.flow'].create(flow_data)

        else:
            pay_order_data.update({
                "pay_status": "4",
                "fail_reason": trade_record.trade_data.get('message') if trade_record.trade_data else "放款失败",
            })
            self.write(pay_order_data)

            self.order_id.write({
                "order_status": "6"
            })
        return 

    def test_pay(self):
        """
        模拟放款成功
        """
        now = fields.Datetime.now()
        pay_order_data = {
            "platform_order_no": f"{int(now.timestamp())}",
            "merchant_order_no": f"{int(now.timestamp())}",
            "pay_complete_time": now,
            "pay_status": "3",
            "pay_complete_time": now,
            "pay_fee": self.payment_setting_id.calc_fee(self.pay_amount)
        }
        self.write(pay_order_data)
        # 财务订单
        self.order_id.write({
            "order_status": "7",
            "pay_complete_time": now,
            "withdraw_time": self.withdraw_time,
        })
        # 生成待还订单
        self.env['repay.order'].create({
            "order_id": self.order_id.id,
            "repay_type": "1",
            "repay_status": "1"
        })
        # 贷超订单
        self.order_id.update_bill_order({
            "bill_status": 2,
            "pending_amount": self.order_id.pending_amount,
            "loan_finish_time": int(now.timestamp()),
            "due_time": int((now+datetime.timedelta(days=self.order_id.loan_period-1)).timestamp())
        })
        self.order_id.update_bill_user_status(update_fields=["product_earliest_due_time", "fst_time_send_out"])

        # 资金流水
        base_data = {
            "order_id": self.order_id.id,
            "product_id": self.product_id.id,
            "payment_setting_id": self.payment_setting_id.id,
            "payment_way_id": self.payment_way_id.id,
            "flow_time": now
        }
        flow_data = []
        if self.pay_amount:
            flow_data.append({
                "flow_type": enums.FLOW_TYPE[0][0],
                "flow_amount": self.pay_amount,
                "trade_type": enums.TRADE_TYPE[0][0],
                **base_data
            })
        if self.order_management_fee:
            flow_data.append({
                **base_data,
                "flow_type": enums.FLOW_TYPE[1][0],
                "flow_amount": self.order_management_fee,
                "trade_type": enums.TRADE_TYPE[1][0],
            })
        if self.pay_fee:
            flow_data.append({
                **base_data,
                "flow_type": enums.FLOW_TYPE[0][0],
                "flow_amount": self.pay_fee,
                "trade_type": enums.TRADE_TYPE[2][0],
            })                      
        self.env['platform.flow'].create(flow_data)
        return


class PayOrderBatchApprovalWizard(models.TransientModel):
    _name = 'pay.order.batch.approval.wizard'
    _description = '批量审核向导'
    _inherit = ['loan.basic.model']

    order_ids = fields.Char(string='订单号', required=True)
    order_count = fields.Integer(string='已选择订单数量', compute='_compute_order_count')
    approval_result = fields.Selection([('2', '通过'), ('3', '拒绝')], string='审核结果')
    remark = fields.Text(string='备注', required=True)

    @api.depends('order_ids')
    def _compute_order_count(self):
        for rec in self:
            order_ids = rec.order_ids.split(',')
            rec.order_count = len(order_ids)

    @api.onchange("approval_result")
    def _onchange_approval_result(self):
        if self.approval_result == '2':
            self.remark = '无异常通过'
        else:
            self.remark = ''

    @api.model
    def create(self, vals):
        obj = super().create(vals)
        for oid in obj.order_ids.split(','):
            order = self.env['loan.order'].browse(int(oid))

            if obj.approval_result == '2':
                self.env['pay.order'].approval_pass(order, obj.remark)
            else:
                self.env['pay.order'].approval_refuse(order, obj.remark)
        return obj


class PayOrderApprovalWizard(models.TransientModel):
    _name = 'pay.order.approval.wizard'
    _description = '单个审核向导'
    _inherit = ['loan.basic.model']

    order_id = fields.Many2one('loan.order', string='订单')
    approval_result = fields.Selection([('2', '通过'), ('3', '拒绝')], string='审核结果')
    amount_desc = fields.Char(string='放款金额')
    remark = fields.Text(string='备注', required=True)

    @api.model
    def create(self, vals):
        obj = super().create(vals)
        if obj.approval_result == '2':
            self.env['pay.order'].approval_pass(obj.order_id, obj.remark)
            
        else:
            self.env['pay.order'].approval_refuse(obj.order_id, obj.remark)
        return obj
    

class PayOrderUpdateWizard(models.TransientModel):
    _name = 'pay.order.update.wizard'
    _description = '订单修改向导'
    _inherit = ['loan.basic.model']

    order_id = fields.Many2one('pay.order', string='订单')
    update_type = fields.Selection([
        ('1', '姓名修改'), 
        ('2', '拒绝订单')
    ], string='修改类型')
    old_name = fields.Char(string='原姓名', related='order_id.order_user_name')
    new_name = fields.Char(string='修改后姓名')

    refuse_remark = fields.Text(string='备注')

    @api.model
    def create(self, vals):
        obj = super().create(vals)
        if obj.update_type == '1':
            obj.order_id.order_id.write({
                "loan_user_name": obj.new_name
            })
        elif obj.update_type == '2':
            now = fields.Datetime.now()
            order_data = {
                "pay_status": "5",
                "refuse_reason": obj.refuse_remark,
                "refuse_time": now
            }
        
            obj.order_id.write(order_data)

            obj.order_id.order_id.write({
                "order_status": "4",
                "refuse_reason": f'财务拒绝: {obj.refuse_remark}',
                "refuse_time": now
            })

            obj.order_id.order_id.update_bill_order({
                "bill_status": 3,
                "refuse_time": int(now.timestamp()),
                "refuse_code": 2
            })

        return obj












