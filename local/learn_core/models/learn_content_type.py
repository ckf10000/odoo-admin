# -*- coding: utf-8 -*-
"""内容类型 — 前端组件注册表 + 存储形态映射"""
from odoo import models, fields


class LearnContentType(models.Model):
    _name = 'learn.content.type'
    _description = '内容类型'
    _order = 'sequence, id'

    name = fields.Char(string='名称', required=True)
    code = fields.Char(string='编码', required=True, index=True)
    storage_model = fields.Selection(
        selection=[
            ('learn.phrase', '字词'),
            ('learn.question', '题目'),
            ('learn.media', '媒体'),
            ('learn.article', '图文'),
        ],
        string='存储模型',
        help='该类型数据存储在哪个模型中',
    )
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)
    has_score = fields.Boolean(string='支持分值', default=False)
    description = fields.Text(string='描述')

    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', '内容类型编码必须唯一！'),
    ]
