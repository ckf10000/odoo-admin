# -*- coding: utf-8 -*-
"""学期 维度表"""
from odoo import models


class LearnDimSemester(models.Model):
    _name = 'learn.dim.semester'
    _description = '学期 维度'
    _inherit = 'learn.dim.mixin'
    _order = 'sequence, id'
