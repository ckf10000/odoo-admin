# -*- coding: utf-8 -*-
import urllib
import logging
import datetime
from odoo import http, fields
from ..utils import pay_utils

_logger = logging.getLogger(__name__)


class LoanOrderController(http.Controller):

    @http.route('/loan_order/create', auth='public', csrf=False, type="json", methods=['POST'])
    def create_loan_order(self, **kw):
        request = http.request
        data = request.get_json_data()
        is_auto_pay = request.env["loan.order.settings"].sudo().get_param('is_auto_pay', False)

        data["apply_time"] = datetime.datetime.fromtimestamp( data['apply_time'] )#.replace(tzinfo=datetime.timezone.utc)

        fields = [
            "loan_user_id", 
            "loan_user_name", 
            "app_id", 
            "bill_id", 
            "product_id", 
            "order_no", 
            "order_status",
            "order_type",
            "apply_time",
            "contract_amount",
            "loan_period",
            "management_fee_rate",
            "management_fee",
            "loan_amount",
            "bank_account_no",
            "bank_ifsc_code"
        ]
        order_data = {
            field: data.get(field, "")
            for field in fields
        }
        order = request.env['loan.order'].sudo().create(order_data)

        if is_auto_pay:
            request.env['pay.order'].sudo().approval_pass(order, "自动放款", is_auto=True)
        return {"order_id": order.id}