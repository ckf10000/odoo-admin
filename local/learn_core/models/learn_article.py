# -*- coding: utf-8 -*-
"""图文内容：知识要点、诗词背诵等"""
from odoo import models, fields


class LearnArticle(models.Model):
    _name = 'learn.article'
    _description = '图文内容'
    _order = 'sequence, id'

    name = fields.Char(string='标题', required=True)
    article_type = fields.Selection(
        selection='_get_article_type_selection',
        string='内容类型',
    )
    content = fields.Html(string='正文', help='富文本内容')
    selector_ids = fields.Many2many(
        'learn.selector', 'learn_article_selector_rel', 'article_id', 'selector_id', string='适用选择器',
    )
    content_edit_mode = fields.Boolean(string='正文编辑模式', default=False)
    cover_image = fields.Binary(string='封面图', attachment=True)
    tags = fields.Char(string='标签')
    description = fields.Text(string='摘要')
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)

    def _get_article_type_selection(self):
        """动态从 learn.content.type 中读取 storage_model='learn.article' 的所有 code"""
        types = self.env['learn.content.type'].sudo().search([
            ('storage_model', '=', 'learn.article'),
        ])
        return [(t.code, t.name) for t in types]

    def action_edit_content(self):
        self.content_edit_mode = True

    def action_save_content(self):
        self.content_edit_mode = False

    def action_cancel_content(self):
        self.content_edit_mode = False
