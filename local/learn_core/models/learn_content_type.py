# -*- coding: utf-8 -*-
"""内容类型"""
from odoo import models, fields


class LearnContentType(models.Model):
    _name = 'learn.content.type'
    _description = '内容类型'
    _order = 'sequence, id'

    name = fields.Char(string='名称', required=True)
    code = fields.Char(string='编码', required=True, index=True)
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)
    description = fields.Text(string='描述')

    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', '内容类型编码必须唯一！'),
    ]
