# -*- coding: utf-8 -*-
"""媒体资源：视频、音频、文件"""
from odoo import models, fields


class LearnMedia(models.Model):
    _name = 'learn.media'
    _description = '媒体资源'
    _order = 'sequence, id'

    name = fields.Char(string='名称', required=True)
    media_type = fields.Selection(
        selection='_get_media_type_selection',
        string='内容类型', required=True,
    )
    url = fields.Char(string='链接', help='视频/音频链接')
    file_data = fields.Binary(string='文件', attachment=True)
    file_name = fields.Char(string='文件名')
    duration = fields.Integer(string='时长（秒）', help='视频/音频时长')
    selector_ids = fields.Many2many(
        'learn.selector', 'learn_media_selector_rel', 'media_id', 'selector_id', string='适用选择器',
    )
    description = fields.Text(string='描述')
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)

    def _get_media_type_selection(self):
        """动态从 learn.content.type 中读取 storage_model='learn.media' 的所有 code"""
        types = self.env['learn.content.type'].sudo().search([
            ('storage_model', '=', 'learn.media'),
        ])
        return [(t.code, t.name) for t in types]
