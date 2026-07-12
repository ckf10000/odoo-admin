# -*- coding: utf-8 -*-
"""单词组 + 组内单词"""
from odoo import models, fields, api


class LearnWordGroup(models.Model):
    _name = 'learn.word.group'
    _description = '单词组'
    _order = 'sequence, id'

    name = fields.Char(string='名称', required=True)
    selector_id = fields.Many2one(
        'learn.selector', string='选择器', required=True, index=True, ondelete='restrict',
    )
    selector_process_id = fields.Many2one(
        'learn.selector.process', string='学习过程', required=True, index=True, ondelete='restrict',
        domain="[('selector_id', '=', selector_id)]",
    )
    # 兼容旧数据
    process_id = fields.Many2one(
        'learn.process', string='学习过程', related='selector_process_id.process_id', store=True,
    )
    description = fields.Text(string='描述')
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)

    line_ids = fields.One2many('learn.word.group.line', 'group_id', string='单词列表')


class LearnWordGroupLine(models.Model):
    _name = 'learn.word.group.line'
    _description = '组内单词'
    _order = 'sequence, id'
    _rec_name = 'display_name'

    group_id = fields.Many2one(
        'learn.word.group', string='单词组', required=True, ondelete='cascade', index=True,
    )
    word_id = fields.Many2one(
        'learn.word', string='单词', required=True, ondelete='restrict', index=True,
    )
    phonetic = fields.Char(string='音标', related='word_id.phonetic')
    meaning = fields.Char(string='释义', related='word_id.meaning')
    sequence = fields.Integer(string='排序', default=10)

    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('word_id.name', 'group_id.name')
    def _compute_display_name(self):
        for r in self:
            r.display_name = f'{r.word_id.name} ({r.group_id.name})'

    _sql_constraints = [
        ('unique_group_word', 'UNIQUE(group_id, word_id)', '该单词已在组内！'),
    ]
