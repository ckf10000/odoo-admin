# -*- coding: utf-8 -*-
"""
res.users 扩展

为 Odoo 用户模型添加与 OAuth2.0 相关的扩展。
"""
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    token_ids = fields.One2many('auth.token', 'user_id', string='OAuth Tokens')

    def action_revoke_all_tokens(self):
        """撤销该用户的所有 Token"""
        self.ensure_one()
        self.token_ids.filtered(lambda t: not t.is_revoked).action_revoke()
        return True
