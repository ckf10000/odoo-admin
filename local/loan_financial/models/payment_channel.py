import logging
import datetime, pytz
from typing import Dict, List
from odoo import models, fields, api
from . import enums
from ..utils import pay_utils


_logger = logging.getLogger(__name__)


class PaymentChannel(models.Model):
    _name = 'payment.channel'
    _description = '支付渠道'
    _inherit = ['loan.basic.model']
    _rec_name = 'channel_name'
    _order = "sequence asc"
    _table = 'F_payment_channel'

    enum_code = fields.Integer(string='枚举编码', required=True)
    channel_name = fields.Char(string='渠道名称', required=True)
    merchant_no = fields.Char(string='商户id')
    merchant_key = fields.Char(string='商户密钥')
    call_back_url = fields.Char(string='回调地址')
    redirect_url = fields.Char(string='跳转地址')
    sequence = fields.Integer(string='排序', default=99)
    payment_way_ids = fields.Many2many('payment.way', 'payment_channel_way_rel', 'cid', 'wid', string='支付方式')

    def call_pay_order(self, amount, loan_order, device="pc"):
        """
        调用代收接口
        """
        self.ensure_one()
        trade_no = self.env['ir.sequence'].sudo().next_by_code('trade_record_no_seq')

        if self.enum_code == 1:
            data = {
                'merchantNo': self.merchant_no,
                'key': self.merchant_key,
                'orderNo': trade_no,
                'amount': str(amount),
                'notifyUrl': self.call_back_url or '',
                'userName': loan_order.loan_user_name,
                'timestamp': datetime.datetime.now().astimezone(tz=pytz.timezone( 'Asia/Kolkata' )).strftime('%Y-%m-%d %H:%M:%S'),
            } 
            res = pay_utils.sf_pay.create_pay_order(data)
            pay_url = res.get('url', '')
            platform_order_no = res.get('platformOrderNo', '')
        else:
            data = {
                'mchId': int(self.merchant_no),
                'key': self.merchant_key,
                'mchOrderNo': trade_no,
                'orderAmount': int(amount * 100),
                'notifyUrl': self.call_back_url or '',
                'returnUrl': self.redirect_url or '',
                'device': device,
                'uid': loan_order.loan_uid,
                'customerName': loan_order.loan_user_name,
                'tel': loan_order.loan_user_phone
            }
            res = pay_utils.coin_pay.create_pay_order(data)
            pay_url = res.get('data', {}).get('payUrl')
            platform_order_no = res.get('data', {}).get('payOrderId', '')
            
        trade_data = {
            'order_id': loan_order.id,
            'payment_setting_id': loan_order.repayment_setting_id.id,
            'payment_way_id': loan_order.repayment_way_id.id,
            'trade_no': trade_no,
            'platform_order_no': platform_order_no,
            'trade_amount': amount,
            'trade_type': '1',
            'trade_start_time': fields.Datetime.now(),
            'trade_data': res,
        }
        return trade_data, pay_url
    
    def call_search_order(self, trade_no):
        """
        待付订单查询接口
        """
        flag = False
        if self.enum_code == 1:
            res = pay_utils.coin_pay.search_order({
                "merchantNo": self.merchant_no,
                "key": self.merchant_key,
                "orderNo": trade_no,
                "timestamp": datetime.datetime.now().astimezone(tz=pytz.timezone( 'Asia/Kolkata' )).strftime('%Y-%m-%d %H:%M:%S')
            })
            status = res.get('status', '')
            if status == "1":
                trade_status = "2"
                flag = True
            
            platform_order_no = res.get('platformOrderNo')
            trade_amount = float(res.get('realAmount', 0) )
            trade_end_time = datetime.datetime.now()

        else:
            res = pay_utils.coin_pay.search_order({
                "mchId": int(self.merchant_no),
                "key": self.merchant_key,
                "payOrderId": trade_no
            })
            status = res.get('data', {}).get('status')
            if status == "5":
                trade_status = "3"
                flag = True
            elif status == "3":
                trade_status = "2"
                flag = True

            platform_order_no = res.get('data', {}).get('payOrderId')
            trade_amount = round(res.get('data', {}).get('orderAmount', 0) / 100, 2)
            trade_end_time = res.get('data', {}).get('paySuccessTime')
            if trade_end_time:
                trade_end_time = datetime.datetime.fromtimestamp(trade_end_time / 1000)
            else:
                trade_end_time = datetime.datetime.now()
            
        trade_data = {
            "trade_status": trade_status,
            "platform_order_no": platform_order_no,
            "trade_amount": trade_amount,
            "trade_end_time": trade_end_time,
            "trade_data": res
        }
        return flag, trade_data

    def call_supplement_order(self, utr, trade_no):
        """
        调用补单接口
        """
        is_success = False
        if self.enum_code == 1:
            data = pay_utils.sf_pay.create_supplement_order({
                "merchantNo": self.merchant_no,
                'key': self.merchant_key,
                "orderNo": trade_no,
                "utr": utr,
                "timestamp": datetime.datetime.now().astimezone(tz=pytz.timezone( 'Asia/Kolkata' )).strftime('%Y-%m-%d %H:%M:%S'),
            })
            if data.get('code') == 0 and data.get('budanResult') == "succ":
                is_success = True
        else:
            data = pay_utils.coin_pay.create_supplement_order({
                'mchId': self.merchant_no,
                'key': self.merchant_key,
                'mchOrderNo': trade_no,
                'utr': utr
            })
            if data['code'] == 200:
                is_success = True
        return is_success, data
        
    def action_fee_setting(self):
        use_type = self.env.context.get('use_type')
        res = self.env['payment.channel.fee'].search([('payment_channel_id', '=', self.id), ('use_type', '=', use_type)], limit=1)
        action_data = {
            'type': 'ir.actions.act_window',
            'res_model': 'payment.channel.fee',
            'res_id': res.id if res else None,
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.form_payment_channel_fee_setting').id,
            'target': 'new',
        }
        context = {
            'dialog_size': 'medium',
        }
        if not res:
            context.update({
                'default_payment_channel_id': self.id,
                'default_use_type': use_type,
            })
        action_data.update({
            'context': context,
        })
        if use_type == '1':
            action_data.update({
                'name': '放款/退款手续费配置',
            })
        else:
            action_data.update({
                'name': '还款手续费配置',
            })

        return action_data


class PaymentChannelFee(models.Model):
    _name = 'payment.channel.fee'
    _description = '支付渠道手续费配置'
    _inherit = ['loan.basic.model']
    _table = 'F_payment_channel_fee'

    payment_channel_id = fields.Many2one('payment.channel', string='支付渠道', required=True, index=True)
    use_type = fields.Selection(enums.PAYMENT_CHANNEL_USE_TYPE, string='渠道使用类型', default='1')

    fee_mode = fields.Selection(selection=enums.CHANNEL_FEE_MODE, string='收费模式', default=enums.CHANNEL_FEE_MODE[0][0])
    base_fee = fields.Float(string='基础费用', default=0)
    fee_rate = fields.Integer(string='费率', default=0)

    fee_line_ids = fields.One2many('payment.channel.fee.line', 'fee_setting_id', string='阶梯费用设置')


class PaymentChannelFeeLine(models.Model):
    _name = 'payment.channel.fee.line'
    _description = '支付渠道手续费阶梯配置'
    _inherit = ['loan.basic.model']
    _table = 'F_payment_channel_fee_line'

    fee_setting_id = fields.Many2one('payment.channel.fee', string='手续费配置', required=True, index=True)
    base_fee = fields.Float(string='基础费用', default=0)
    fee_rate = fields.Integer(string='费率', default=0)

    day_count_start = fields.Integer(string='日交易次数起始', default=0)
    day_count_end = fields.Integer(string='日交易次数结束', default=1)

    month_count_start = fields.Integer(string='月交易次数起始', default=0)
    month_count_end = fields.Integer(string='月交易次数结束', default=1)


class PaymentWay(models.Model):
    _name = 'payment.way'
    _description = '支付方式'
    _inherit = ['loan.basic.model']
    _rec_name = 'way_name'
    _order = "sequence asc"
    _table = 'F_payment_way'

    enum_code = fields.Integer(string='枚举编码', required=True)
    way_name = fields.Char(string='方式名称', required=True)
    sequence = fields.Integer(string='排序', required=True)
    payment_channel_ids = fields.Many2many('payment.channel', 'payment_channel_way_rel', 'wid', 'cid', string='支付渠道')
    
    
class PaymentSetting(models.Model):
    _name = 'payment.setting'
    _description = 'Payment Setting'
    _inherit = ['loan.basic.model']
    _table = 'F_payment_setting'
    _rec_name = 'payment_channel_id'

    use_type = fields.Selection(enums.PAYMENT_CHANNEL_USE_TYPE, string='渠道使用类型', default='1')
    payment_channel_id = fields.Many2one('payment.channel', string='支付渠道', required=True, auto_join=True)
    payment_way_id = fields.Many2one('payment.way', string='支付方式', required=True)
    status = fields.Boolean(string='状态', default=True)

    payment_product_ids = fields.One2many('loan.product', 'payment_setting_id', string='适用产品')
    repayment_product_ids = fields.One2many('loan.product', 'repayment_setting_id', string='适用产品')

    trade_record_ids = fields.One2many('payment.setting.trade.record', 'payment_setting_id', string='交易记录')

    def calc_fee(self, amount: float) -> float:
        """
        计算手续费
        """
        fee_setting = self.env['payment.channel.fee'].search([('payment_channel_id', '=', self.payment_channel_id.id), ('use_type', '=', self.use_type)])
        if not fee_setting:
            return 0.0
        
        if fee_setting.fee_mode == enums.CHANNEL_FEE_MODE[0][0]:
            fee = round(fee_setting.base_fee + (amount * fee_setting.fee_rate / 100), 2)
            return fee
        else:
            now = fields.Datetime.today()
            
            day_trade_count = len(self.trade_record_ids.filtered(lambda x: x.trade_start_time.date() == now and x.trade_status == '2'))
            month_trade_count = len(self.trade_record_ids.filtered(
                lambda x: x.trade_start_time.year == now.year and x.trade_start_time.month == now.month and x.trade_status == '2'
            ))
    
            day_fee, month_fee = 0, 0
            for i in fee_setting.fee_line_ids:
                if day_trade_count >= i.day_count_start and (day_trade_count <= i.day_count_end or i.day_count_end == 0):
                    day_fee = round(i.base_fee + (amount * i.fee_rate / 100), 2)
                    
                if month_trade_count >= i.month_count_start and (month_trade_count <= i.month_count_end or i.month_count_end == 0):
                    month_fee = round(i.base_fee + (amount * i.fee_rate / 100), 2)
                    
                if day_fee and month_fee:
                    break
            
            return day_fee if day_fee <= month_fee else month_fee
    
    def web_save(self, vals, specification: Dict[str, Dict], next_id=None) -> List[Dict]:
        payment_product_ids = []
        for i in vals.pop('payment_product_ids', []):
            payment_product_ids.append(i[1])
        
        repayment_product_ids = []
        for i in vals.pop('repayment_product_ids', []):
            repayment_product_ids.append(i[1])

        if self:
            self.write(vals)
        else:
            self = self.create(vals)

        for pid in payment_product_ids:
            self.env['loan.product'].browse(pid).update({'payment_setting_id': self.id})
        for pid in repayment_product_ids:
            self.env['loan.product'].browse(pid).update({'repayment_setting_id': self.id})

        if next_id:
            self = self.browse(next_id)
        return self.with_context(bin_size=True).web_read(specification)

    def action_create(self):
        """
        列表点击新增按钮
        """
        use_type = self.env.context.get('default_use_type', "1")
        return {
            'name': '新增',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'target': 'new',
            'context': {'dialog_size': 'large', "default_use_type": use_type}
        }
    
    def action_fee_setting(self):
        use_type = self.env.context.get('default_use_type')
        action_data = {
            'type': 'ir.actions.act_window',
            'res_model': 'payment.channel.fee.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.form_payment_channel_fee_setting_wizard').id,
            'target': 'new',
            'context':{
                'dialog_size': 'medium',
                'default_use_type': use_type
            }
        }
        return action_data
    

class PaymentSettingTradeRecord(models.Model):
    _name = 'payment.setting.trade.record'
    _description = 'Payment Setting Trade Record'
    _inherit = ['loan.basic.model']
    _table = 'F_payment_setting_trade_record'

    order_id = fields.Many2one('loan.order', string='订单', index=True)
    payment_setting_id = fields.Many2one('payment.setting', string='支付渠道')
    payment_way_id = fields.Many2one('payment.way', string='支付方式')
    trade_amount = fields.Float(string='交易金额')
    trade_status = fields.Selection([('1', '已发起'), ('2', '已成功'), ('3', '已失败')], string='交易状态', index=True)
    trade_no = fields.Char(string='交易流水号', required=True, index=True)
    trade_type = fields.Selection([('1', '代收'), ('2', '代付')], string='交易类型', index=True)
    trade_start_time = fields.Datetime(string='交易发起时间', required=True, index=True)
    trade_end_time = fields.Datetime(string='交易完成时间')
    platform_order_no = fields.Char(string='平台订单号')
    trade_params = fields.Json(string='交易参数')
    trade_data = fields.Json(string='交易结果数据')

    res_id = fields.Integer(string='关联记录ID')
    res_model = fields.Char(string='关联记录模型')

    @api.model
    def task_search_order(self):
        """
        订单查询
        """
        now = fields.Datetime.now() - datetime.timedelta(hours=12)
        objs = self.search([('trade_status', '=', '1'), ('trade_type', '=', "2"), ("trade_start_time", "<=", now)])
        for obj in objs:
            flag, trade_data = obj.payment_setting_id.payment_channel_id.call_search_order(obj.trade_no)
            if not flag:
                continue

            obj.update_data(trade_data)
            
    def update_data(self, data):
        """
        {
            "trade_no": xxx, # 交易单号
            "trade_status": "", # 交易状态
            "platform_order_no": "", # 平台订单号
            "trade_amount: 0, # 交易金额
            "trade_end_time": "", # 交易完成时间

            "trade_data: {}
        }
        """
        self.write(data)
        res_record = self.env[self.res_model].sudo().browse(self.res_id)
        res_record.after_payment(self)


class PaymentChannelFeeWizard(models.TransientModel):
    _name = 'payment.channel.fee.wizard'
    _description = 'Payment Channel Fee Wizard'

    use_type = fields.Selection(enums.PAYMENT_CHANNEL_USE_TYPE, string='渠道使用类型', default='1')
    payment_setting_id = fields.Many2one('payment.setting', string='支付渠道', required=True, domain='[("use_type", "=", use_type)]')

    fee_mode = fields.Selection(selection=enums.CHANNEL_FEE_MODE, string='收费模式')
    base_fee = fields.Float(string='基础费用', default=0)
    fee_rate = fields.Integer(string='费率', default=0)

    fee_line_ids = fields.One2many('payment.channel.fee.wizard.line', 'wizard_id', string='阶梯费用设置')

    @api.onchange('payment_setting_id')
    def _onchange_payment_setting_id(self):
        fee_setting = self.env['payment.channel.fee'].search([
            ('payment_channel_id', '=', self.payment_setting_id.payment_channel_id.id),
            ("use_type", "=", self.payment_setting_id.use_type)
        ])
        if not fee_setting:
            return
        
        self.fee_mode = fee_setting.fee_mode
        self.base_fee = fee_setting.base_fee
        self.fee_rate = fee_setting.fee_rate

        self.fee_line_ids = False

        self.fee_line_ids = [
            (0, 0, {
                'base_fee': i.base_fee, 
                'fee_rate': i.fee_rate, 
                'day_count_start': i.day_count_start, 
                'day_count_end': i.day_count_end,
                'month_count_start': i.month_count_start,
                'month_count_end': i.month_count_end
            })
            for i in fee_setting.fee_line_ids
        ]
    
    @api.model
    def create(self, vals):
        obj = super().create(vals)

        fee_setting = self.env['payment.channel.fee'].search([
            ('payment_channel_id', '=', obj.payment_setting_id.payment_channel_id.id),
            ("use_type", "=", obj.use_type)
        ], limit=1)
        if not fee_setting:
            self.env['payment.channel.fee'].create({
                'payment_channel_id': obj.payment_setting_id.payment_channel_id.id,
                'use_type': obj.use_type,
                'fee_mode': obj.fee_mode,
                'base_fee': obj.base_fee,
                'fee_rate': obj.fee_rate,
                'fee_line_ids': [
                    (0, 0, {
                        'base_fee': i.base_fee, 
                        'fee_rate': i.fee_rate, 
                        'day_count_start': i.day_count_start, 
                        'day_count_end': i.day_count_end,
                        'month_count_start': i.month_count_start,
                        'month_count_end': i.month_count_end
                    })
                    for i in obj.fee_line_ids
                ]
            })
        else:
            fee_setting.fee_line_ids.unlink()

            fee_setting.write({
                'fee_mode': obj.fee_mode,
                'base_fee': obj.base_fee,
                'fee_rate': obj.fee_rate,
                'fee_line_ids':[
                    (0, 0, {
                        'base_fee': i.base_fee, 
                        'fee_rate': i.fee_rate, 
                        'day_count_start': i.day_count_start, 
                        'day_count_end': i.day_count_end,
                        'month_count_start': i.month_count_start,
                        'month_count_end': i.month_count_end
                    })
                    for i in obj.fee_line_ids
                ]
            })

        return obj


class PaymentChannelFeeWizardLine(models.TransientModel):
    _name = 'payment.channel.fee.wizard.line'
    _description = 'Payment Channel Fee Wizard'

    wizard_id = fields.Many2one('payment.channel.fee.wizard', string='手续费配置', required=True, index=True)
    base_fee = fields.Float(string='基础费用', default=0)
    fee_rate = fields.Integer(string='费率', default=0)

    day_count_start = fields.Integer(string='日交易次数起始', default=0)
    day_count_end = fields.Integer(string='日交易次数结束', default=1)

    month_count_start = fields.Integer(string='月交易次数起始', default=0)
    month_count_end = fields.Integer(string='月交易次数结束', default=1)

    