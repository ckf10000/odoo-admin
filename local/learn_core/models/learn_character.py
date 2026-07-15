# -*- coding: utf-8 -*-
"""生字库"""
from odoo import models, fields


class LearnCharacter(models.Model):
    _name = 'learn.character'
    _description = '生字'
    _order = 'sequence, id'

    name = fields.Char(string='生字', required=True, index=True)
    pinyin = fields.Char(string='拼音')
    strokes = fields.Integer(string='笔画')
    radical = fields.Char(string='部首')
    meaning = fields.Text(string='释义')
    phrases = fields.Text(string='组词')

    source_ids = fields.Many2many(
        'learn.content.source', 'learn_character_source_rel', 'character_id', 'source_id', string='来源',
    )
    difficulty = fields.Selection([
        ('easy', '简单'),
        ('medium', '中等'),
        ('hard', '困难'),
    ], string='难度', default='easy')

    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)
    description = fields.Text(string='备注')

    group_line_ids = fields.One2many('learn.group.line', 'character_id', string='所属内容组')

    _sql_constraints = [
        ('unique_character', 'UNIQUE(name)', '该生字已存在！'),
    ]
