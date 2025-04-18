import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Merchant(models.Model):
    _name = 'loan.merchant'
    _description = 'Merchant'
    _inherit = ['loan.basic.model']
    _table = 'T_merchant'

    name = fields.Char(string='商户名称', required=True)


class ProductTotalAmountType(models.Model):
    _name = 'loan.product.total.amount.type'
    _description = 'Total Amount Type'
    _order = 'sequence'
    _rec_name = 'type_name'
    _table = "T_defer_total_amount_type"

    enum_code = fields.Integer(string='枚举编码', required=True)
    type_name = fields.Char(string='模式名称', required=True)
    sequence = fields.Integer(string='排序', required=True)


class Product(models.Model):
    _name = 'loan.product'
    _description = 'Product'
    _inherit = ['loan.basic.model']
    _table = 'T_product'
    _rec_name = 'product_name'
    _order = 'product_code desc'

    product_code = fields.Char(string='产品ID', required=True, index=True)
    product_name = fields.Char(string='产品名称', required=True, index=True)
    status = fields.Boolean(string='状态', required=True)
    merchant_id = fields.Many2one('loan.merchant', string='商户名称', required=True, ondelete='restrict')
    min_amount = fields.Integer(string='首贷金额最小值', required=True)
    max_amount = fields.Integer(string='首贷金额最大值', required=True)
    display_first_loan_amount = fields.Char(string='首贷金额', compute='_compute_first_loan_amount')

    defer_allowed = fields.Boolean(string='是否允许展期', required=True)
    defer_period_from = fields.Integer(string='展期允许期之起始日')
    defer_period_to = fields.Integer(string='展期允许期之终止日')
    display_defer_period = fields.Char(string='允许展期时间', compute='_compute_defer_period')
    defer_interest_rate = fields.Float(string='展期利率')
    display_defer_interest_rate = fields.Char(string='展期利率', compute='_compute_display_defer_interest_rate')

    defer_min_on_credit_amount = fields.Integer(string='展期最小挂账金额', required=True)
    # defer_quota = fields.Selection(enums.DEFER_QUOTA, string="展期总额度", default="1", required=True)
    defer_total_amount_type_id = fields.Many2one('loan.product.total.amount.type', string='关联展期总额度', required=True)
    defer_total_amount_type = fields.Char('展期总额度', compute="_compute_defer_total_amount_type", store=True)
    overdue_fine = fields.Float(string='滞纳金', required=True)
    penalty_interest_rate = fields.Float(string='罚息利率', required=True)
    display_penalty_interest_rate = fields.Char(string='罚息利率', compute='_compute_display_penalty_interest_rate')

    admin_fee_rate = fields.Float(string='管理费利率', required=True)
    display_admin_fee_rate = fields.Char(string='管理费利率', compute='_compute_display_admin_fee_rate')
    
    @api.depends('min_amount', 'max_amount')
    def _compute_first_loan_amount(self):
        for record in self:
            record.display_first_loan_amount = str(record.min_amount) + '~' + str(record.max_amount)

    @api.depends('defer_period_from', 'defer_period_to')
    def _compute_defer_period(self):
        for record in self:
            record.display_defer_period = str(record.defer_period_from) + '-' + str(record.defer_period_to)

    @api.depends('defer_interest_rate')
    def _compute_display_defer_interest_rate(self):
           for record in self:
            record.display_defer_interest_rate = f'{int(record.defer_interest_rate * 100)}%'

    @api.depends('penalty_interest_rate')
    def _compute_display_penalty_interest_rate(self):
        for record in self:
            record.display_penalty_interest_rate = f'{int(record.penalty_interest_rate * 100)}%'

    @api.depends('admin_fee_rate')
    def _compute_display_admin_fee_rate(self):
        for record in self:
            record.display_admin_fee_rate = f'{int(record.admin_fee_rate * 100)}%'

    @api.depends('defer_total_amount_type_id')
    def _compute_defer_total_amount_type(self):
        for record in self:
            record.defer_total_amount_type = str(record.defer_total_amount_type_id.enum_code)