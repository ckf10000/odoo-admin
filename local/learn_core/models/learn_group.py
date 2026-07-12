# -*- coding: utf-8 -*-
"""通用内容组 + 组内条目"""
from odoo import models, fields, api


class LearnGroup(models.Model):
    _name = 'learn.group'
    _description = '内容组'
    _order = 'sequence, id'

    name = fields.Char(string='名称', required=True)
    selector_id = fields.Many2one(
        'learn.selector', string='选择器', required=True, index=True, ondelete='restrict',
    )
    selector_process_id = fields.Many2one(
        'learn.selector.process', string='学习过程', required=True, index=True, ondelete='restrict',
        domain="[('selector_id', '=', selector_id)]",
    )
    process_id = fields.Many2one(
        'learn.process', string='学习过程', related='selector_process_id.process_id', store=True,
    )

    description = fields.Text(string='描述')
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)

    line_ids = fields.One2many('learn.group.line', 'group_id', string='内容列表')


class LearnGroupLine(models.Model):
    _name = 'learn.group.line'
    _description = '组内条目'
    _order = 'sequence, id'
    _rec_name = 'display_name'

    group_id = fields.Many2one(
        'learn.group', string='内容组', required=True, ondelete='cascade', index=True,
    )
    content_type_id = fields.Many2one(
        'learn.content.type', string='内容类型', required=True, index=True, ondelete='restrict',
        default=lambda self: self.env.ref('learn_core.content_type_word', raise_if_not_found=False),
    )
    content_type = fields.Char(string='类型编码', compute='_compute_content_type')

    @api.depends('content_type_id.code')
    def _compute_content_type(self):
        for r in self:
            r.content_type = r.content_type_id.code or ''

    title = fields.Char(string='标题', compute='_compute_title', store=True)

    # ---- 单词 ----
    word_id = fields.Many2one(
        'learn.word', string='单词', ondelete='restrict', index=True,
    )
    phonetic = fields.Char(string='音标', related='word_id.phonetic')
    meaning = fields.Char(string='释义', related='word_id.meaning')

    # ---- 视频 ----
    video_title = fields.Char(string='视频标题')
    video_url = fields.Char(string='视频地址')
    video_duration = fields.Integer(string='时长（秒）')

    # ---- 文件 ----
    file_name = fields.Char(string='文件名')
    file_data = fields.Binary(string='文件')

    # ---- 知识要点 ----
    knowledge_title = fields.Char(string='要点标题')
    knowledge_content = fields.Text(string='要点内容')

    # ---- 公共 ----
    sequence = fields.Integer(string='排序', default=10)
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('word_id.name', 'video_title', 'file_name', 'knowledge_title')
    def _compute_title(self):
        for r in self:
            r.title = r.word_id.name or r.video_title or r.file_name or r.knowledge_title or '-'

    @api.depends('title', 'group_id.name')
    def _compute_display_name(self):
        for r in self:
            r.display_name = f'{r.title} ({r.group_id.name})'

    _sql_constraints = [
        ('unique_group_word', 'UNIQUE(group_id, word_id)', '该单词已在组内！'),
    ]
