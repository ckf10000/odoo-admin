# -*- coding: utf-8 -*-
"""学习选择器（业务主表）"""
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LearnSelector(models.Model):
    _name = 'learn.selector'
    _description = '学习选择器'
    _order = 'sequence, id'

    name = fields.Char(string='显示名称', compute='_compute_name', store=True)
    code = fields.Char(string='唯一编码', compute='_compute_code', store=True, index=True)
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)
    description = fields.Text(string='备注')

    # ---- 8 个维度外键（region 为一对多）----
    category_id = fields.Many2one('learn.dim.category', string='分类', required=True, index=True, ondelete='restrict')
    stage_id = fields.Many2one('learn.dim.stage', string='阶段', index=True, ondelete='restrict')
    class_id = fields.Many2one('learn.dim.class', string='班级/年级', index=True, ondelete='restrict')
    region_ids = fields.Many2many('learn.dim.region', 'learn_selector_region_rel', 'selector_id', 'region_id',
                                  string='地区')
    subject_id = fields.Many2one('learn.dim.subject', string='科目', index=True, ondelete='restrict')
    year_id = fields.Many2one('learn.dim.year', string='年份', index=True, ondelete='restrict')
    semester_id = fields.Many2one('learn.dim.semester', string='学期', index=True, ondelete='restrict')
    version_id = fields.Many2one('learn.dim.version', string='版本', index=True, ondelete='restrict')

    # ---- 学习过程分类（多对多，带顺序）----
    process_rel_ids = fields.One2many('learn.selector.process', 'selector_id', string='学习过程分类')

    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', '该选择器组合已存在！'),
    ]

    def write(self, vals):
        if 'region_ids' in vals:
            for record in self:
                new_ids = set()
                for cmd in vals['region_ids']:
                    # 收集最终保留的 region_ids
                    if cmd[0] == 6:  # (6, 0, [ids])
                        new_ids = set(cmd[2])
                        break
                    elif cmd[0] == 4:  # (4, id)
                        new_ids = set(record.region_ids.ids) | {cmd[1]}
                    elif cmd[0] == 3:  # (3, id) — 删除
                        new_ids = set(record.region_ids.ids) - {cmd[1]}
                    elif cmd[0] == 1:  # (1, id, vals)
                        new_ids = set(record.region_ids.ids)
                    elif cmd[0] == 0:  # (0, 0, vals)
                        new_ids = set(record.region_ids.ids)

                # 处理 (5,) / (2, id) 等清除/全删命令
                removed_ids = set(record.region_ids.ids) - new_ids \
                    if new_ids else set(record.region_ids.ids)

                if removed_ids:
                    blocked = self.env['learn.selector.process'].sudo().search([
                        ('selector_id', '=', record.id),
                        ('region_id', 'in', list(removed_ids)),
                    ], limit=1)
                    if blocked:
                        raise ValidationError(
                            f'地区 "{blocked.region_id.name}" 已被过程"{blocked.process_id.name}"引用，'
                            f'请先删除该过程关联再解绑地区。'
                        )
        return super().write(vals)

    @api.depends('category_id', 'stage_id', 'class_id', 'subject_id',
                 'year_id', 'semester_id', 'version_id')
    def _compute_name(self):
        for r in self:
            parts = []
            for f in ['category_id', 'stage_id', 'class_id', 'version_id', 'year_id', 'semester_id', 'subject_id']:
                if r[f]:
                    parts.append(r[f].name)
            r.name = ' / '.join(filter(None, parts))

    _code_fields = ['category_id', 'stage_id', 'class_id', 'version_id', 'year_id', 'semester_id', 'subject_id']

    @api.depends(*_code_fields)
    def _compute_code(self):
        for r in self:
            parts = []
            for f in self._code_fields:
                parts.append(r[f].code if r[f] else '_')
            r.code = '_'.join(parts)
