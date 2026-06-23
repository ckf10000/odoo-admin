# -*- coding: utf-8 -*-
"""
OAuth2.0 客户端模型

管理注册的第三方客户端（Android App、iOS App、Web 前端等）。
"""
import secrets

from odoo import models, fields, api


class AuthClient(models.Model):
    """OAuth2.0 客户端"""
    _name = 'auth.client'
    _description = 'OAuth2.0 Client'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char('客户端名称', required=True, help="例如：Android App、iOS App")
    client_id = fields.Char(
        'Client ID',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: self._generate_client_id(),
        help="客户端唯一标识",
    )
    client_secret = fields.Char(
        'Client Secret',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: self._generate_client_secret(),
        help="客户端密钥，用于刷新 Token",
    )
    description = fields.Text('描述')
    active = fields.Boolean('启用', default=True)

    # Token 有效期配置
    access_token_expiry = fields.Integer(
        'Access Token 有效期(小时)',
        default=2,
        required=True,
        help="Access Token 过期时间，默认 2 小时",
    )
    refresh_token_expiry = fields.Integer(
        'Refresh Token 有效期(天)',
        default=30,
        required=True,
        help="Refresh Token 过期时间，默认 30 天",
    )

    # 统计
    token_ids = fields.One2many('auth.token', 'client_id', string='Tokens')
    token_count = fields.Integer('活跃 Token 数', compute='_compute_token_count')
    log_ids = fields.One2many('auth.log', 'client_id', string='登录日志')

    _sql_constraints = [
        ('client_id_unique', 'unique(client_id)', 'Client ID 必须唯一！'),
    ]

    @api.depends('token_ids')
    def _compute_token_count(self):
        for client in self:
            client.token_count = len(client.token_ids.filtered(lambda t: not t.is_revoked))

    @api.model
    def _generate_client_id(self):
        """生成 32 位 Client ID"""
        return secrets.token_hex(16)

    @api.model
    def _generate_client_secret(self):
        """生成 64 位 Client Secret"""
        return secrets.token_hex(32)

    def action_revoke_all_tokens(self):
        """撤销该客户端的所有 Token"""
        self.ensure_one()
        self.token_ids.filtered(lambda t: not t.is_revoked).action_revoke()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '成功',
                'message': '已撤销所有活跃 Token',
                'type': 'success',
            }
        }

    def _get_or_create_default_client(self):
        """获取或创建默认客户端"""
        default = self.search([('name', '=', 'Default Client')], limit=1)
        if not default:
            default = self.create({
                'name': 'Default Client',
                'description': '系统默认客户端，用于快速开始',
            })
        return default
