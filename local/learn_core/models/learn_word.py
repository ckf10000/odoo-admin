# -*- coding: utf-8 -*-
"""单词库"""
from odoo import models, fields, api


class LearnWord(models.Model):
    _name = 'learn.word'
    _description = '单词'
    _order = 'sequence, id'

    name = fields.Char(string='单词', required=True, index=True)
    phonetic = fields.Char(string='音标')
    pos_ids = fields.Many2many(
        'learn.word.pos', 'learn_word_pos_rel', 'word_id', 'pos_id', string='词性',
    )
    meaning = fields.Char(string='中文释义', index=True)
    meaning_en = fields.Text(string='英文释义')
    example_sentence = fields.Text(string='例句')
    phrases = fields.Text(string='关联短语')
    etymology = fields.Text(string='词源解释')

    source_ids = fields.Many2many(
        'learn.content.source', 'learn_word_source_rel', 'word_id', 'source_id', string='来源',
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

    @api.model_create_multi
    def create(self, vals_list):
        new_vals = []
        existing_records = self.browse()
        for vals in vals_list:
            existing = self.sudo().search([('name', '=', vals.get('name'))], limit=1)
            if existing:
                # 如果已存在，追加新的 source_ids
                new_sources = vals.get('source_ids')
                if new_sources:
                    existing.sudo().write({'source_ids': new_sources})
                existing_records += existing
                continue
            new_vals.append(vals)
        records = super().create(new_vals) if new_vals else self.browse()
        return records + existing_records

    _sql_constraints = [
        ('unique_word', 'UNIQUE(name)', '该单词已存在！'),
    ]
