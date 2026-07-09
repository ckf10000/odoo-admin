# -*- coding: utf-8 -*-
"""班级/年级 维度表"""
from odoo import models


class LearnDimKlass(models.Model):
    _name = 'learn.dim.class'
    _description = '班级/年级 维度'
    _inherit = 'learn.dim.mixin'
    _order = 'sequence, id'
