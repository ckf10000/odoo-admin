# -*- coding: utf-8 -*-
"""通用内容组 + 章节 + 组内条目"""
from odoo import models, fields, api
from odoo.exceptions import ValidationError


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
    )
    selector_process_id = fields.Many2one(
        'learn.selector.process', string='选择器-过程',
        compute='_compute_selector_process', store=True,
    )

    description = fields.Text(string='描述')
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)

    section_ids = fields.One2many('learn.group.section', 'group_id', string='章节列表')

    @api.onchange('selector_id')
    def _onchange_selector_id(self):
        process_ids = []
        if self.selector_id and self.selector_id.profile_id:
            process_ids = self.selector_id.profile_id.process_line_ids.process_id.ids
        self.process_id = False
        return {'domain': {'process_id': [('id', 'in', process_ids)]}}

    def _compute_process_domain(self):
        for r in self:
            process_ids = []
            if r.selector_id and r.selector_id.profile_id:
                process_ids = r.selector_id.profile_id.process_line_ids.process_id.ids
            r.process_domain_ids = [(6, 0, process_ids)]

    process_domain_ids = fields.Many2many(
        'learn.process', string='可用过程',
        compute='_compute_process_domain',
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        Section = self.env['learn.group.section'].sudo()
        for record in records:
            if not record.section_ids:
                Section.create({
                    'group_id': record.id,
                    'name': '默认章节',
                    'content_type_id': self.env.ref('learn_core.content_type_word_card', raise_if_not_found=False).id,
                    'sequence': 10,
                })
        return records

    def ensure_default_section_type(self, storage_model):
        """确保默认章节的 content_type 与存储模型匹配"""
        self.ensure_one()
        default_sec = self.section_ids[:1]
        if default_sec and default_sec.name == '默认章节' and default_sec.content_type_id.storage_model != storage_model:
            # 找到匹配的 content_type
            ct = self.env['learn.content.type'].sudo().search([
                ('storage_model', '=', storage_model),
            ], limit=1)
            if ct:
                default_sec.content_type_id = ct

    def action_create_default_section(self):
        """为当前 group 创建默认章节（如果还没有）"""
        Section = self.env['learn.group.section'].sudo()
        for record in self:
            if not record.section_ids:
                Section.create({
                    'group_id': record.id,
                    'name': '默认章节',
                    'content_type_id': self.env.ref('learn_core.content_type_word_card', raise_if_not_found=False).id,
                    'sequence': 10,
                })

    @api.depends('selector_id', 'process_id')
    def _compute_selector_process(self):
        for r in self:
            sp = self.env['learn.selector.process'].sudo().search([
                ('selector_id', '=', r.selector_id.id),
                ('process_id', '=', r.process_id.id),
            ], limit=1)
            r.selector_process_id = sp.id if sp else False


class LearnGroupSection(models.Model):
    _name = 'learn.group.section'
    _description = '内容组章节'
    _order = 'sequence, id'

    group_id = fields.Many2one(
        'learn.group', string='内容组', required=True, ondelete='cascade', index=True,
    )
    name = fields.Char(string='章节名称', required=True)
    content_type_id = fields.Many2one(
        'learn.content.type', string='内容类型', required=True, index=True, ondelete='restrict',
    )
    content_type = fields.Char(string='类型编码', related='content_type_id.code', store=True)
    storage_model = fields.Selection(string='存储模型', related='content_type_id.storage_model', store=True)

    sequence = fields.Integer(string='排序', default=10)
    score = fields.Float(string='本章节满分', default=0.0, help='0 表示不计分')
    description = fields.Text(string='描述')

    line_ids = fields.One2many('learn.group.line', 'section_id', string='条目列表')


class LearnGroupLine(models.Model):
    _name = 'learn.group.line'
    _description = '组内条目'
    _order = 'sequence, id'
    _rec_name = 'display_name'

    section_id = fields.Many2one(
        'learn.group.section', string='所属章节', ondelete='cascade', index=True,
    )
    group_id = fields.Many2one(
        'learn.group', string='内容组', related='section_id.group_id', store=True, index=True,
    )

    # ---- Generic Reference ----
    res_model = fields.Selection(
        selection=[
            ('learn.word', '字词'),
            ('learn.character', '生字'),
            ('learn.question', '题目'),
            ('learn.media', '媒体'),
            ('learn.article', '图文'),
        ],
        string='引用模型',
    )
    res_id = fields.Integer(string='引用记录 ID', index=True)

    # ---- 便捷字段 ----
    word_id = fields.Many2one(
        'learn.word', string='字词',
        compute='_compute_ref', inverse='_inverse_ref', store=True,
    )
    question_id = fields.Many2one(
        'learn.question', string='题目',
        compute='_compute_ref', inverse='_inverse_ref', store=True,
    )
    media_id = fields.Many2one(
        'learn.media', string='媒体',
        compute='_compute_ref', inverse='_inverse_ref', store=True,
    )
    article_id = fields.Many2one(
        'learn.article', string='图文',
        compute='_compute_ref', inverse='_inverse_ref', store=True,
    )
    character_id = fields.Many2one(
        'learn.character', string='生字',
        compute='_compute_ref', inverse='_inverse_ref', store=True,
    )

    # ---- 条目属性 ----
    sequence = fields.Integer(string='排序', default=10)
    score = fields.Float(string='分值', default=0.0, help='0 表示使用默认分值')

    # ---- 显示 ----
    title = fields.Char(string='标题', compute='_compute_title', store=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('res_model', 'res_id')
    def _compute_ref(self):
        for r in self:
            r.word_id = r.res_id if r.res_model == 'learn.word' else False
            r.character_id = r.res_id if r.res_model == 'learn.character' else False
            r.question_id = r.res_id if r.res_model == 'learn.question' else False
            r.media_id = r.res_id if r.res_model == 'learn.media' else False
            r.article_id = r.res_id if r.res_model == 'learn.article' else False

    def _inverse_ref(self):
        for r in self:
            if r.word_id:
                r.res_model = 'learn.word'
                r.res_id = r.word_id.id
            elif r.character_id:
                r.res_model = 'learn.character'
                r.res_id = r.character_id.id
            elif r.question_id:
                r.res_model = 'learn.question'
                r.res_id = r.question_id.id
            elif r.media_id:
                r.res_model = 'learn.media'
                r.res_id = r.media_id.id
            elif r.article_id:
                r.res_model = 'learn.article'
                r.res_id = r.article_id.id

    @api.depends('word_id.name', 'character_id.name', 'question_id.stem', 'media_id.name', 'article_id.name')
    def _compute_title(self):
        for r in self:
            r.title = (
                    r.word_id.name or r.character_id.name or r.question_id.stem
                    or r.media_id.name or r.article_id.name or '-'
            )

    @api.depends('title', 'section_id.name')
    def _compute_display_name(self):
        for r in self:
            r.display_name = f'{r.title} ({r.section_id.name})'

    _sql_constraints = [
        ('unique_section_item', 'UNIQUE(section_id, res_model, res_id)',
         '该内容已在章节中！'),
    ]

    def _check_content_type(self):
        """校验 res_model 与 section.content_type.storage_model 一致"""
        for line in self:
            if not line.res_model or not line.res_id:
                continue
            expected = line.section_id.content_type_id.storage_model
            if not expected:
                continue
            if line.res_model != expected:
                # 如果是默认章节，自动修正类型
                if line.section_id.name == '默认章节':
                    ct = self.env['learn.content.type'].sudo().search([
                        ('storage_model', '=', line.res_model),
                    ], limit=1)
                    if ct:
                        line.section_id.content_type_id = ct
                        continue
                raise ValidationError(
                    f'[{line.section_id.name}] 内容类型要求引用 {expected}，当前为 {line.res_model}'
                )

    @api.model_create_multi
    def create(self, vals_list):
        groups_to_fix = set()
        for vals in vals_list:
            # 如果传了 group_id 但没传 section_id，自动挂默认章节
            if vals.get('group_id') and not vals.get('section_id'):
                group = self.env['learn.group'].browse(vals['group_id'])
                default_sec = group.section_ids[:1] if group.section_ids else None
                if default_sec:
                    vals['section_id'] = default_sec.id
            if not vals.get('res_model') and vals.get('section_id'):
                section = self.env['learn.group.section'].browse(vals['section_id'])
                vals['res_model'] = section.content_type_id.storage_model
            # 如果明确传了 word_id / question_id / media_id / article_id，自动设 res_model
            if vals.get('word_id') and not vals.get('res_model'):
                vals['res_model'] = 'learn.word'
            if vals.get('question_id') and not vals.get('res_model'):
                vals['res_model'] = 'learn.question'
            if vals.get('media_id') and not vals.get('res_model'):
                vals['res_model'] = 'learn.media'
            if vals.get('article_id') and not vals.get('res_model'):
                vals['res_model'] = 'learn.article'
            if vals.get('res_model') and vals.get('section_id'):
                groups_to_fix.add(vals['section_id'])
        records = super().create(vals_list)
        # 同步默认章节的 content_type
        for line in records:
            if line.section_id and line.res_model:
                line.section_id.group_id.ensure_default_section_type(line.res_model)
        records._check_content_type()
        return records

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('skip_content_type_check'):
            self._check_content_type()
        return res
