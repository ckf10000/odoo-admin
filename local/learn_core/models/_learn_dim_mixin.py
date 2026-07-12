# -*- coding: utf-8 -*-
"""维度表公共 Mixin"""
from odoo import models, fields
from odoo.exceptions import ValidationError

# 维度模型 → selector 字段名 映射
_DIM_FIELD_MAP = {
    'learn.dim.category': 'category_id',
    'learn.dim.stage': 'stage_id',
    'learn.dim.class': 'class_id',
    'learn.dim.region': 'region_ids',  # Many2many
    'learn.dim.subject': 'subject_id',
    'learn.dim.year': 'year_id',
    'learn.dim.semester': 'semester_id',
    'learn.dim.version': 'version_id',
}


class LearnDimMixin(models.AbstractModel):
    _name = 'learn.dim.mixin'
    _description = '维度表公共字段'
    _order = 'sequence, id'

    name = fields.Char(string='名称', required=True, translate=True)
    code = fields.Char(string='编码', required=True)
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)
    icon = fields.Binary(string='图标', help='App 端显示的图标')
    description = fields.Text(string='描述')

    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', '编码必须唯一！'),
    ]

    def unlink(self):
        field_name = _DIM_FIELD_MAP.get(self._name)
        if field_name:
            for record in self:
                if field_name == 'region_ids':
                    blocked = self.env['learn.selector'].sudo().search([
                        (field_name, 'in', [record.id]),
                    ], limit=1)
                else:
                    blocked = self.env['learn.selector'].sudo().search([
                        (field_name, '=', record.id),
                    ], limit=1)
                if blocked:
                    raise ValidationError(
                        f'"{record.name}" 已被选择器 "{blocked.name}" 引用，无法删除。'
                    )
        return super().unlink()
