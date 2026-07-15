# -*- coding: utf-8 -*-
"""字词桥接层：连接知识库原子数据到 selector"""
from odoo import models, fields, api


class LearnPhrase(models.Model):
    _name = 'learn.phrase'
    _description = '字词'
    _order = 'sequence, id'

    name = fields.Char(string='名称', compute='_compute_name', store=True)

    # ---- 桥接到知识库原子数据 ----
    ref_model = fields.Selection([
        ('learn.word', '单词'),
        ('learn.character', '生字'),
    ], string='来源模型', required=True)
    ref_int = fields.Integer(string='来源记录号', index=True)

    phrase_type = fields.Selection(
        selection='_get_phrase_type_selection',
        string='内容类型', required=True, default='word_card',
    )

    # ---- 便捷引用 ----
    word_id = fields.Many2one(
        'learn.word', string='单词',
        compute='_compute_ref', inverse='_inverse_ref', store=True,
    )
    character_id = fields.Many2one(
        'learn.character', string='生字',
        compute='_compute_ref', inverse='_inverse_ref', store=True,
    )

    # ---- 关联选择器 ----
    selector_ids = fields.Many2many(
        'learn.selector', 'learn_phrase_selector_rel', 'phrase_id', 'selector_id', string='适用选择器',
    )

    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)
    description = fields.Text(string='备注')

    group_line_ids = fields.One2many('learn.group.line', 'phrase_id', string='所属内容组')

    def _get_phrase_type_selection(self):
        types = self.env['learn.content.type'].sudo().search([
            ('storage_model', '=', 'learn.phrase'),
        ])
        return [(t.code, t.name) for t in types]

    @api.depends('ref_model', 'ref_int')
    def _compute_ref(self):
        for r in self:
            if r.ref_model == 'learn.word' and r.ref_int:
                r.word_id = r.ref_int
                r.character_id = None
            elif r.ref_model == 'learn.character' and r.ref_int:
                r.character_id = r.ref_int
                r.word_id = None
            else:
                r.word_id = None
                r.character_id = None

    @api.depends('word_id.name', 'character_id.name')
    def _compute_name(self):
        for r in self:
            r.name = (r.word_id.name or r.character_id.name or '-')

    def _inverse_ref(self):
        for r in self:
            if r.word_id:
                r.ref_model = 'learn.word'
                r.ref_int = r.word_id.id
            elif r.character_id:
                r.ref_model = 'learn.character'
                r.ref_int = r.character_id.id
