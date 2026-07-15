# -*- coding: utf-8 -*-
"""通用内容来源：单词/生字/题目等共用"""
from odoo import models, fields


class LearnContentSource(models.Model):
    _name = 'learn.content.source'
    _description = '内容来源'
    _order = 'sequence, id'

    name = fields.Char(string='名称', required=True)
    code = fields.Char(string='编码', required=True)
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)
    description = fields.Text(string='描述')

    word_ids = fields.Many2many(
        'learn.word', 'learn_word_source_rel', 'source_id', 'word_id', string='单词列表',
    )
    character_ids = fields.Many2many(
        'learn.character', 'learn_character_source_rel', 'source_id', 'character_id', string='生字列表',
    )

    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', '来源编码必须唯一！'),
    ]
