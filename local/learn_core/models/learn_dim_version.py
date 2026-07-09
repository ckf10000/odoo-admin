# -*- coding: utf-8 -*-
"""版本 维度表"""
from odoo import models


class LearnDimVersion(models.Model):
    _name = 'learn.dim.version'
    _description = '版本 维度'
    _inherit = 'learn.dim.mixin'
    _order = 'sequence, id'
