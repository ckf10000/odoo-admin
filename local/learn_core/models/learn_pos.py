# -*- coding: utf-8 -*-
"""词性字典"""
from odoo import models, fields


class LearnWordPOS(models.Model):
    _name = 'learn.word.pos'
    _description = '词性'
    _order = 'sequence, id'

    name = fields.Char(string='中文名', required=True)
    code = fields.Char(string='编码', required=True, index=True)
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)
