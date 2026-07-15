# -*- coding: utf-8 -*-
"""过程配置模板：selector 通过绑定 Profile 间接获得过程列表"""
from odoo import models, fields, api


class LearnSubjectProfile(models.Model):
    _name = 'learn.subject.profile'
    _description = '过程配置模板'
    _order = 'sequence, id'

    name = fields.Char(string='名称', required=True)
    process_line_ids = fields.One2many(
        'learn.subject.profile.process', 'profile_id', string='学习过程',
    )
    sequence = fields.Integer(string='排序值', default=10)

    sequence_str = fields.Char(string='排序', compute='_compute_sequence_str', store=True)

    @api.depends('sequence')
    def _compute_sequence_str(self):
        for r in self:
            r.sequence_str = str(r.sequence)

    active = fields.Boolean(string='启用', default=True)
    description = fields.Text(string='描述')

    selector_ids = fields.One2many('learn.selector', 'profile_id', string='关联选择器')

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', '模板名称已存在！'),
    ]


class LearnSubjectProfileProcess(models.Model):
    _name = 'learn.subject.profile.process'
    _description = '模板-过程关联'
    _order = 'sequence, id'

    profile_id = fields.Many2one(
        'learn.subject.profile', string='模板', required=True, ondelete='cascade', index=True,
    )
    process_id = fields.Many2one(
        'learn.process', string='学习过程', required=True, ondelete='cascade', index=True,
    )
    sequence = fields.Integer(string='排序值', default=10)

    sequence_str = fields.Char(string='排序', compute='_compute_sequence_str', store=True)

    @api.depends('sequence')
    def _compute_sequence_str(self):
        for r in self:
            r.sequence_str = str(r.sequence)

    _sql_constraints = [
        ('unique_profile_process', 'UNIQUE(profile_id, process_id)',
         '该过程已在模板中！'),
    ]
