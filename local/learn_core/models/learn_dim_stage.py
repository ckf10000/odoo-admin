# -*- coding: utf-8 -*-
"""阶段 维度表"""
from odoo import models


class LearnDimStage(models.Model):
    _name = 'learn.dim.stage'
    _description = '阶段 维度'
    _inherit = 'learn.dim.mixin'
    _order = 'sequence, id'
