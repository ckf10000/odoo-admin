import logging
import datetime
from odoo import models, fields, api
from . import enums
from ..utils import date_utils


_logger = logging.getLogger(__name__)


class LoanOrder(models.Model):
    _inherit = ['loan.order']

    extension_amount = fields.Float('展期金额', compute="_compute_extension_amount", store=True)  #todo 计算展期应付金额

    extension_record_ids = fields.One2many('extension.record', 'order_id', '展期记录')
    extension_payed_amount = fields.Float('已还展期金额', digits=(16, 2))

    @api.depends()
    def _compute_extension_amount(self):
        """
        a. 展期应付金额=订单申请展期应支付的展期费用金额；
        b. 展期应付金额=展期总额度*展期利率，展期总额度=“合同金额”或“挂账金额”，具体以后台配置为准（贷超-产品管理-产品配置-“展期利率”、“展期总额度”）；
        c. 展期费用取整逻辑: 假设展期费用小数点后第一位数字为X, 若X≤4, 则展期费用向下取整, 若X>4,则展期费用向上取整。
        """
        for record in self:
            if record.product_id.defer_total_amount_type == "1":  # 合同金额
                extension_amount = record.contract_amount
            else:  # 挂账金额
                extension_amount = record.pending_amount * record.product_id.defer_interest_rate
            
            record.extension_amount = round(extension_amount)

    def action_show_extension_wizard(self):
        return
        return {
            'name': '展期',
            'type': 'ir.actions.act_window',
            'res_model': 'extension.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
            }
        }