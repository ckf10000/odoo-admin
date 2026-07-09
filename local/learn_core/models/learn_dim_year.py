# -*- coding: utf-8 -*-
"""年份 维度表"""
from odoo import models


class LearnDimYear(models.Model):
    _name = 'learn.dim.year'
    _description = '年份 维度'
    _inherit = 'learn.dim.mixin'
    _order = 'sequence, id'
