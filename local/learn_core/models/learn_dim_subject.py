# -*- coding: utf-8 -*-
"""科目 维度表"""
from odoo import models


class LearnDimSubject(models.Model):
    _name = 'learn.dim.subject'
    _description = '科目 维度'
    _inherit = 'learn.dim.mixin'
    _order = 'sequence, id'
