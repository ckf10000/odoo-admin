# -*- coding: utf-8 -*-
import urllib
import logging
import datetime, pytz
from odoo import http, fields
from ..utils import pay_utils

_logger = logging.getLogger(__name__)


class PayController(http.Controller):

    @http.route('/finance/get_pay_link', auth='public', csrf=False, type="json", methods=['POST'])
    def get_pay_link(self, **kw):
        request = http.request
        data = request.get_json_data()
        trade_no = request.env['ir.sequence'].sudo().next_by_code('trade_record_no_seq')
        order = request.env['loan.order'].sudo().search([('order_no', '=', data['order_no'])], limit=1)
        repay_order = request.env['repay.order'].sudo().search([('order_id', '=', order.id)], limit=1)
        payment_channel = order.repayment_setting_id.payment_channel_id

        if payment_channel.enum_code == 2:
            data = {
                'mchId': int(payment_channel.merchant_no),
                'key': payment_channel.merchant_key,
                'mchOrderNo': trade_no,
                'orderAmount': int(order.pending_amount * 100),
                'notifyUrl': payment_channel.call_back_url or "",
                'returnUrl': payment_channel.redirect_url or "",
                'device': data.get('device', 'android'),
                'uid': order.loan_uid,
                'customerName': order.loan_user_name,
                'tel': order.loan_user_phone
            }
            res = pay_utils.coin_pay.create_pay_order(data)
            pay_url = res.get('data', {}).get('payUrl')
            platform_order_no = res.get('data', {}).get('payOrderId')
        else:
            data = {
                'merchantNo': payment_channel.merchant_no,
                'key': payment_channel.merchant_key,
                'orderNo': trade_no,
                'amount': str(order.pending_amount),
                'notifyUrl': payment_channel.call_back_url or "",
                'userName': order.loan_user_name,
                'timestamp': datetime.datetime.now().astimezone(tz=pytz.timezone( 'Asia/Kolkata' )).strftime('%Y-%m-%d %H:%M:%S'),
            } 
            res = pay_utils.sf_pay.create_pay_order(data)
            pay_url = res.get('url', "")
            platform_order_no = res.get('platformOrderNo', '')

        # 创建交易记录
        trade_data = {
            'order_id': order.id,
            'payment_setting_id': order.repayment_setting_id.id,
            'payment_way_id': order.repayment_way_id.id,
            'trade_amount': order.pending_amount,
            'trade_no': trade_no,
            'trade_status': '1' if res.get('code', 999) == 200 else '3',
            'trade_type': '1',
            'trade_start_time': fields.Datetime.now(),
            'platform_order_no': platform_order_no,
            'trade_data': res,
            'res_model': 'repay.order',
            'res_id': repay_order.id
        }
        request.env['payment.setting.trade.record'].sudo().create(trade_data)
        
        res = {
            "payUrl": pay_url
        }
        return res


    @http.route('/finance/pay_callback', auth='public', csrf=False, type="json", methods=['POST'])
    def pay_callback(self, **kw):
        """
        {
            "trade_channel": "coinpay", # 支付渠道 sfpay、coinpay
            "trade_data: { # 原始数据（支付接口返回）
                code: int = Field(description="支付接口类型", alias='code')
                mch_id: int = Field(description="商户ID", alias='mchId')
                mch_order_no: str = Field(description="商户订单号", alias='mchOrderNo')
                product_id: int = Field(description="支付产品ID", alias='productId')
                order_amount: int = Field(description="订单金额", alias='orderAmount')
                pay_order_id: str = Field(description="平台订单号", alias='payOrderId')
                utr: str = Field(default="", description="utr", alias='utr')
                pay_success_time: int = Field(default=None, description="支付成功时间戳(毫秒)", alias='paySuccessTime')
                message: str = Field(default=None, description="成功就固定值success 失败返回失败原因", alias='message')
                extra: str = Field(default="", description="附加参数", alias='extra')
                sign: str = Field(description="签名", alias='sign')
            }
        }
        """
        data = http.request.get_json_data()
        trade_channel = data.get('trade_channel')
        trade_data = data.get('trade_data')
        if trade_channel == 'coinpay':
            trade_no = trade_data.get('mchOrderNo')
            trade_status = "2" if trade_data.get("code") == 1 else "3"
            platform_order_no = trade_data.get('payOrderId')
            trade_amount = round(trade_data.get('orderAmount', 0) / 100, 2)
            trade_end_time = trade_data.get('paySuccessTime')
            if trade_end_time:
                trade_end_time = datetime.datetime.fromtimestamp(trade_end_time / 1000)
            else:
                trade_end_time = datetime.datetime.now()
        else:
            trade_no = trade_data.get('orderNo')
            status = trade_data.get("status")
            if status == "1":
                trade_status = "2"
            elif status == "3":
                trade_status = "3"
            else:
                trade_status = "1"

            platform_order_no = trade_data.get('platformOrderNo')
            trade_amount = float(trade_data.get('realAmount', 0) )
            trade_end_time = datetime.datetime.now()
        
        trade_data = {
            "trade_no": trade_no,
            "trade_status": trade_status,
            "platform_order_no": platform_order_no,
            "trade_amount": trade_amount,
            "trade_end_time": trade_end_time,
            "trade_data": trade_data
        }
        trade_recode = http.request.env['payment.setting.trade.record'].sudo().search([('trade_no', '=', trade_no)], limit=1)

        trade_recode.sudo().update_data(trade_data)
        return 'success'
    
    @http.route('/finance/update_bank_info', auth='public', csrf=False, type="json", methods=['POST'])
    def update_bank_info(self, **kw):
        """
        修改银行卡信息, 自动调用支付
        """
        data = http.request.get_json_data()
        order = http.request.env['loan.order'].sudo().search([('order_no', '=', data.get('order_no'))], limit=1)
        bank_account = http.request.env['bank.account'].sudo().browse(data.get('bank_account_id'))

        order.sudo().write({
            "bank_account_no": bank_account.account_no,
            "bank_ifsc_code": bank_account.ifsc_code,
            "order_status": "5"
        })
        pay_order = order.sudo().get_pay_order()
        pay_order.sudo().write({"modify_account_status": "3", "pay_status": "2"})
        pay_order.sudo().action_payment_again()
        return 'success'



