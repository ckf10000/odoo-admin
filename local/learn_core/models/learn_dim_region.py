# -*- coding: utf-8 -*-
"""地区 维度表"""
from odoo import models


class LearnDimRegion(models.Model):
    _name = 'learn.dim.region'
    _description = '地区 维度'
    _inherit = 'learn.dim.mixin'
    _order = 'sequence, id'
