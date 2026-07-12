# -*- coding: utf-8 -*-
"""单词库"""
from odoo import models, fields


class LearnWord(models.Model):
    _name = 'learn.word'
    _description = '单词库'
    _order = 'sequence, id'

    name = fields.Char(string='单词', required=True, index=True)
    phonetic = fields.Char(string='音标')
    part_of_speech = fields.Selection([
        ('noun', '名词'),
        ('verb', '动词'),
        ('adj', '形容词'),
        ('adv', '副词'),
        ('prep', '介词'),
        ('conj', '连词'),
        ('pron', '代词'),
        ('num', '数词'),
        ('art', '冠词'),
        ('interj', '感叹词'),
        ('phrase', '短语'),
        ('other', '其他'),
    ], string='词性')
    meaning = fields.Char(string='中文释义', index=True)
    meaning_en = fields.Text(string='英文释义')
    example_sentence = fields.Text(string='例句')
    phrases = fields.Text(string='关联短语')
    etymology = fields.Text(string='词源解释')

    source_ids = fields.Many2many(
        'learn.word.source', 'learn_word_source_rel', 'word_id', 'source_id', string='来源',
    )
    difficulty = fields.Selection([
        ('easy', '简单'),
        ('medium', '中等'),
        ('hard', '困难'),
    ], string='难度', default='easy')

    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)
    description = fields.Text(string='备注')

    group_line_ids = fields.One2many('learn.group.line', 'word_id', string='所属内容组')

    _sql_constraints = [
        ('unique_word', 'UNIQUE(name)', '该单词已存在！'),
    ]
