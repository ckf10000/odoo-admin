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
    process_id = fields.Many2one(
        'learn.process', string='学习过程', required=True, index=True, ondelete='restrict',
        domain="[('selector_rel_ids.selector_id', '=', selector_id)]",
    )
    selector_process_id = fields.Many2one(
        'learn.selector.process', string='选择器-过程', compute='_compute_selector_process', store=True,
    )

    @api.depends('selector_id', 'process_id')
    def _compute_selector_process(self):
        for r in self:
            sp = self.env['learn.selector.process'].sudo().search([
                ('selector_id', '=', r.selector_id.id),
                ('process_id', '=', r.process_id.id),
            ], limit=1)
            r.selector_process_id = sp.id if sp else False

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
    content_type = fields.Selection([
        ('word', '单词'),
        ('video', '视频'),
        ('file', '文件'),
    ], string='内容类型', default='word', required=True)

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

    # ---- 公共 ----
    sequence = fields.Integer(string='排序', default=10)

    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('word_id.name', 'video_title', 'file_name', 'group_id.name')
    def _compute_display_name(self):
        for r in self:
            title = r.word_id.name or r.video_title or r.file_name or '-'
            r.display_name = f'{title} ({r.group_id.name})'

    _sql_constraints = [
        ('unique_group_word', 'UNIQUE(group_id, word_id)', '该单词已在组内！'),
    ]
