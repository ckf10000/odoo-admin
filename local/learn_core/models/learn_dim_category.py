# -*- coding: utf-8 -*-
"""分类 维度表"""
from odoo import models


class LearnDimCategory(models.Model):
    _name = 'learn.dim.category'
    _description = '分类 维度'
    _inherit = 'learn.dim.mixin'
    _order = 'sequence, id'
