# -*- coding: utf-8 -*-
import urllib
import logging
import datetime, pytz
from odoo import http, fields
from ..utils import pay_utils

_logger = logging.getLogger(__name__)


class PayController(http.Controller):

    @http.route('/finance/get_extension_detail', auth='public', csrf=False, type="json", methods=['POST'])
    def get_extension_detail(self, **kw):
        request = http.request
        data = request.get_json_data()
        order = request.env['loan.order'].sudo().search([('order_no', '=', data['order_no'])], limit=1)
        if not order:
            return {'extension_amount': 0, 'pending_amount': 0}
        extension_rec = request.env['extension.record'].sudo().search([('order_id', '=', order.id)], limit=1)
        if extension_rec:
            return {
                "extension_amount": extension_rec.extension_amount if extension_rec else 0,
                "pending_amount": extension_rec.pending_amount if extension_rec else 0,
            }
        extension_amount = order.compute_extension_amount()
        return {
            "extension_amount": extension_amount,
            "pending_amount": extension_amount
        }

    @http.route('/finance/apply_extension', auth='public', csrf=False, type="json", methods=['POST'])
    def apply_extension(self, **kw):
        request = http.request
        data = request.get_json_data()
        order = request.env['loan.order'].sudo().search([('order_no', '=', data['order_no'])], limit=1)

        # 获取或者创建展期记录
        extension = request.env['extension.record'].sudo().search([('order_id', '=', order.id), ("status", "not in", ["5", "6"])], limit=1)
        if not extension:
            extension = request.env['extension.record'].sudo().create({
                'order_id': order.id,
                'status': "1",
                'extension_days': order.loan_period,
                'extension_amount': order.compute_extension_amount(),
                'order_repay_date': order.repay_date,
            })
        res = {
            "payUrl": extension.get_pay_link(device=data.get('device', 'android'))
        }
        return res

        