import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class ProductQuantityNode(models.Model):
    _name = 'loan.product.quantity.node'
    _description = 'Product Quantity Node'
    _order = 'sequence'
    _rec_name = 'node_name'
    _table = 'T_bill_proc_node'

    node_name = fields.Char(string='节点名称', required=True)
    enum_code = fields.Integer(string='枚举编码', required=True)
    sequence = fields.Integer(string='排序', required=True)


class ProductQuantity(models.Model):
    _name = 'loan.product.quantity'
    _description = 'Product Quantity'
    _inherit = ['loan.basic.model']
    _table = 'T_quantity'

    product_id = fields.Many2one('loan.product', string='产品名称', ondelete="restrict")
    product_code = fields.Char(string='产品ID', related='product_id.product_code', store=True)
    merchant_id = fields.Many2one('loan.merchant', string='商户', related='product_id.merchant_id', store=True)
    daily_fst_loan_old_type = fields.Selection([('1', '不限'), ('2', '自定义')], string='每日首贷老客进件量类型', default='1', required=True)
    daily_fst_loan_old_limit = fields.Integer(string='每日首贷老客进件量')
    display_daily_fst_loan_old_limit = fields.Char(string='每日首贷老客进件量', compute='_compute_display_daily_fst_loan_old_limit')

    daily_fst_loan_new_type = fields.Selection([('1', '不限'), ('2', '自定义')], string='每日首贷新客进件量类型', default='1', required=True)
    daily_fst_loan_new_limit = fields.Integer(string='每日首贷新客进件量')
    display_daily_fst_loan_new_limit = fields.Char(string='每日首贷新客进件量', compute='_compute_display_daily_fst_loan_new_limit')

    daily_fst_loantotal_type = fields.Selection([('1', '不限'), ('2', '自定义')], string='每日首贷总进件量类型', default='1', required=True)
    daily_fst_loan_total_limit = fields.Integer(string='每日首贷总进件量')
    display_daily_fst_loan_total_limit = fields.Char(string='每日首贷总进件量', compute='_compute_display_daily_fst_loan_total_limit')

    node_id = fields.Many2one('loan.product.quantity.node', string='进件节点', default=lambda self: self.env['loan.product.quantity.node'].search([], limit=1), required=True)
    status = fields.Boolean(string='状态', default=True, required=True)

    @api.depends('daily_fst_loan_old_limit')
    def _compute_display_daily_fst_loan_old_limit(self):
        for record in self:
            record.display_daily_fst_loan_old_limit = str(record.daily_fst_loan_old_limit) if record.daily_fst_loan_old_limit != -1 else '不限'
    
    @api.depends('daily_fst_loan_new_limit')
    def _compute_display_daily_fst_loan_new_limit(self):
        for record in self:
            record.display_daily_fst_loan_new_limit = str(record.daily_fst_loan_new_limit) if record.daily_fst_loan_new_limit != -1 else '不限'

    @api.depends('daily_fst_loan_total_limit')
    def _compute_display_daily_fst_loan_total_limit(self):
        for record in self:
            record.display_daily_fst_loan_total_limit = str(record.daily_fst_loan_total_limit) if record.daily_fst_loan_total_limit != -1 else '不限'

    @api.model
    def _check_data(self, data):
        """
        检查数据
        """
        errors = []
        # 每日首贷老客进件量
        if data.get('daily_fst_loan_old_type') == "2" and data.get('daily_fst_loan_old_limit', 0) < 0:
            errors.append('每日首贷老客进件量请输入≥0的整数')
        
        # 每日首贷新客进件量
        if data.get('daily_fst_loan_new_type') == "2" and data.get('daily_fst_loan_new_limit', 0) < 0:
            errors.append('每日首贷新客进件量请输入≥0的整数')

        # 每日首贷总进件量
        if data.get('daily_fst_loantotal_type') == "2" and data.get('daily_fst_loan_total_limit', 0) < 0:
            errors.append('每日首贷总进件量请输入≥0的整数')

        if errors:
            raise exceptions.ValidationError(self.format_action_error(errors))

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if val.get('daily_fst_loan_old_type', '1'):
                val['daily_fst_loan_old_limit'] = -1
            if val.get('daily_fst_loan_new_type', '1'):
                val['daily_fst_loan_new_limit'] = -1
            if val.get('daily_fst_loantotal_type', '1'):
                val['daily_fst_loan_total_limit'] = -1
        objs = super().create(vals_list)
        return objs
    
    @api.onchange('daily_fst_loan_old_type')
    def _onchange_daily_fst_loan_old_type(self):
        if self.daily_fst_loan_old_type == '1':
            self.daily_fst_loan_old_limit = -1 

    @api.onchange('daily_fst_loan_new_type')
    def _onchange_daily_fst_loan_new_type(self):
        if self.daily_fst_loan_new_type == '1':
            self.daily_fst_loan_new_limit = -1

    @api.onchange('daily_fst_loantotal_type')
    def _onchange_daily_fst_loantotal_type(self):
        if self.daily_fst_loantotal_type == '1':
            self.daily_fst_loan_total_limit = -1