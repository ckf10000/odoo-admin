import logging
from odoo import models, fields, api, exceptions

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
    _inherit = ['loan.product']
    _order = 'product_code desc'

    matrix_id = fields.Many2one('joint.loan.matrix', string='共贷矩阵', required=True, index=True, ondelete='restrict')

    @api.model
    def _action_default_size(self):
        return 'large'
    
    @api.model
    def _action_default_data(self):
        return {
            'default_status': True,
            'default_defer_allowed': True
        }

    @api.model
    def _check_data(self, product_info):
        """
        检查产品信息, 并一次性抛出所有错误
        """
        errors = []
        exist_products = {}

        for pro in self.search([]):
            exist_products.setdefault(pro.product_name, []).append(pro.id)

        # 名称校验
        if 'product_name' in product_info:
            product_name = product_info['product_name']
            if product_name.count('  '):
                errors.append('产品名称中不能有连续空格, 请调整')
            
            exist_pro_ids = exist_products.get(product_name, [])
            if exist_pro_ids and product_info.get('id') not in exist_pro_ids:
                errors.append('该产品名称已使用，请更换名称')
        
        # 首贷金额校验
        min_amount = product_info.get('min_amount', 1)
        max_amount = product_info.get('max_amount', 2)
        if min_amount <= 0 or min_amount > max_amount:
            errors.append('首贷金额值必须>0, 且第1个输入框数值≤第2个输入框数值')

        # 展期相关校验，需要允许展期
        if product_info.get('defer_allowed', True):
            # 允许展期时间校验
            defer_period_from = product_info.get('defer_period_from', 0)
            defer_period_to = product_info.get('defer_period_to', 0)
            if defer_period_from > 0 or defer_period_from > defer_period_to:
                errors.append('允许展期时间请输入负整数, 且第1个输入框数值≤第2个输入框数值')

            # 展期利率
            defer_interest_rate = product_info.get('defer_interest_rate', 0)
            if defer_interest_rate < 0 or defer_interest_rate > 1:
                errors.append('展期利率请输入0-100之间的数值')
            
            # 展期最小挂账金额
            defer_min_on_credit_amount = product_info.get('defer_min_on_credit_amount', 0)
            if defer_min_on_credit_amount <= 0:
                errors.append('展期最小挂账金额需>0')

        # 滞纳金
        overdue_fine = product_info.get('overdue_fine', 0)
        if overdue_fine < 0:
            errors.append('滞纳金请输入≥0的数值')
        
        # 罚息利率
        penalty_interest_rate = product_info.get('penalty_interest_rate', 0)
        if penalty_interest_rate < 0 or penalty_interest_rate > 1:
            errors.append('罚息利率请输入0-100之间的数值')
        
        # 管理费率
        admin_fee_rate = product_info.get('management_fee_interest_rate', 0)
        if admin_fee_rate < 0 or admin_fee_rate > 1:
            errors.append('管理费率请输入0-100之间的数值')

        if errors:
            raise exceptions.ValidationError(self.format_action_error(errors))

    @api.model
    def create(self, val):
        self._check_data(val)
        
        val['product_code'] = self.env['ir.sequence'].next_by_code('product_code_seq')
        obj = super().create(val)

        # 初始化单量配置
        obj.init_quantity()
        return obj
    
    def init_quantity(self):
        self.env['loan.product.quantity'].create([{"product_id": self.id}])