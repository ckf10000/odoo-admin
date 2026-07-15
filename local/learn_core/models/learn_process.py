# -*- coding: utf-8 -*-
"""学习过程分类 + 选择器关联"""
from odoo import models, fields, api


class LearnProcess(models.Model):
    _name = 'learn.process'
    _description = '学习过程分类'
    _order = 'sequence, id'

    name = fields.Char(string='名称', required=True)
    code = fields.Char(string='编码', required=True)
    sequence = fields.Integer(string='排序值', default=10)
    active = fields.Boolean(string='启用', default=True)
    description = fields.Text(string='描述')

    selector_rel_ids = fields.One2many('learn.selector.process', 'process_id', string='关联选择器')

    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', '该学习过程编码已存在！'),
    ]


class LearnSelectorProcess(models.Model):
    _name = 'learn.selector.process'
    _description = '选择器-学习过程关联'
    _order = 'sequence, id'
    _rec_name = 'display_name'

    selector_id = fields.Many2one(
        'learn.selector', string='选择器', required=True, ondelete='cascade', index=True,
    )
    process_id = fields.Many2one(
        'learn.process', string='学习过程', required=True, ondelete='cascade', index=True,
    )
    region_id = fields.Many2one(
        'learn.dim.region', string='地区', ondelete='restrict',
    )
    sequence = fields.Integer(string='排序值', default=10)
    sequence_str = fields.Char(string='排序', compute='_compute_sequence_str', store=True)

    # 辅助字段：region_id 非空则取 id，否则为 0，用于唯一约束（NULL 不参与唯一性检测）
    region_key = fields.Integer(string='地区键', compute='_compute_region_key', store=True, index=True)

    display_name = fields.Char(string='显示名称', compute='_compute_display_name', store=True)

    _sql_constraints = [
        ('unique_selector_process_region',
         'UNIQUE(selector_id, process_id, region_key)',
         '同一选择器下，相同地区和过程只能绑定一次！'),
    ]

    @api.depends('sequence')
    def _compute_sequence_str(self):
        for r in self:
            r.sequence_str = str(r.sequence)

    @api.depends('region_id')
    def _compute_region_key(self):
        for r in self:
            r.region_key = r.region_id.id or 0

    @api.depends('selector_id.name', 'process_id.name', 'region_id.name')
    def _compute_display_name(self):
        for r in self:
            parts = [r.process_id.name]
            if r.region_id:
                parts.append(r.region_id.name)
            r.display_name = ' - '.join(parts)
