# -*- coding: utf-8 -*-
"""维度表公共 Mixin"""
from odoo import models, fields


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
