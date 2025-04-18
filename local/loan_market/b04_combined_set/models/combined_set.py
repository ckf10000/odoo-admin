import logging
from odoo import models, fields, api, exceptions

from ..utils import config


_logger = logging.getLogger(__name__)


class CombinedSet(models.Model):
    _name = 'loan.combined.set'
    _description = 'Combined Set'
    _inherit = ['loan.basic.model']
    _rec_name = 'cs_name'
    _order = 'priority desc'
    _table = 'T_combined_set'

    cs_name = fields.Char(string='合集名称', required=True, index=True, size=config.CombinedSetConfig.MAX_length_cs_name)
    max_num_reloan_products = fields.Integer(string='复贷产品上限', required=True, default=config.CombinedSetConfig.DFT_max_reloan_product_num)
    max_num_new_products = fields.Integer(string='新产品上限', required=True, default=config.CombinedSetConfig.DFT_max_new_product_num)
    priority = fields.Integer(string='优先级', required=True)
    min_amount = fields.Integer(string='额度区间最小值', required=True)
    max_amount = fields.Integer(string='额度区间最大值', required=True)
    display_quota_range = fields.Char(string='合集额度区间', compute='_compute_display_quota_range')

    @api.depends('min_amount', 'max_amount')
    def _compute_display_quota_range(self):
        for record in self:
            record.display_quota_range = f'{record.min_amount} ~ {record.max_amount}'

    @api.model
    def _check_data(self, data):
        """
        检查数据, 并一次性抛出所有错误
        """
        errors = []
        exist_names = {}
        exist_priority = {}

        for rec in self.search([]):
            exist_names.setdefault(rec.cs_name, []).append(rec.id)
            exist_priority.setdefault(rec.priority, []).append(rec.id)

        # 名称校验
        cs_name = data['cs_name']
        if cs_name.count('  '):
            errors.append('合集名称中不能连续的空格，请调整')
        
        exist_ids = exist_names.get(cs_name, [])
        if exist_ids and data.get('id') not in exist_ids:
            errors.append('合集名称已使用，请更换名称')

        # 复贷产品数量上限
        max_num_reloan_products = data.get('max_num_reloan_products', 0)
        if max_num_reloan_products < 0:
            errors.append('复贷产品上限请输入≥0的整数')
        
        # 新产品数量上限
        max_num_new_products = data.get('max_num_new_products', 0)
        if max_num_new_products < 0:
            errors.append('新产品上限请输入≥0的整数')
        
        if max_num_reloan_products + max_num_new_products < 2:
            errors.append('需满足：复贷产品上限+新产品上限≥2')

        # 合集额度区间
        min_amount = data.get('min_amount', 0)
        max_amount = data.get('max_amount', 0)
        if min_amount <= 0 or min_amount > max_amount:
            errors.append('合集额度必须输入>0的数值, 且第1个输入框数值≤第2个输入框数值')
        
        # 优先级
        priority = data.get('priority', 0)
        exist_ids = exist_priority.get(priority, [])
        if exist_ids and data.get('id') not in exist_ids:
            errors.append('优先级值已存在，请调整数值')

        if errors:
            raise exceptions.ValidationError(self.format_action_error(errors))
        
    