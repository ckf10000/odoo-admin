# -*- coding: utf-8 -*-

from odoo import fields, models


class ResUsersSettings(models.Model):
    _inherit = 'res.users.settings'

    list_search_mode = fields.Selection([
        ('odoo', 'Odoo模式'), 
        ('classical', '传统模式')
    ], string='列表搜索模式', default="classical")