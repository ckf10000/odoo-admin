# -*- coding: utf-8 -*-
"""
OAuth2.0 Token 模型

管理 Access Token 和 Refresh Token 的生命周期。
"""
import secrets
import hashlib
from datetime import timedelta

from odoo import models, fields, api, _  # noqa
from odoo.exceptions import AccessDenied


class AuthToken(models.Model):
    """OAuth2.0 Token"""
    _name = 'auth.token'
    _description = 'OAuth2.0 Token'
    _order = 'create_date desc'
    _rec_name = 'access_token'

    user_id = fields.Many2one('res.users', string='用户', required=True, ondelete='cascade', index=True)
    client_id = fields.Many2one('auth.client', string='客户端', required=True, ondelete='cascade', index=True)

    access_token = fields.Char(
        'Access Token',
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self._generate_token(),
    )
    refresh_token = fields.Char(
        'Refresh Token',
        required=True,
        readonly=True,
        default=lambda self: self._generate_token(),
    )

    access_token_hash = fields.Char('Access Token Hash', compute='_compute_hashes', store=True)
    refresh_token_hash = fields.Char('Refresh Token Hash', compute='_compute_hashes', store=True)

    expires_at = fields.Datetime('Access Token 过期时间', required=True, index=True)
    refresh_expires_at = fields.Datetime('Refresh Token 过期时间', required=True)

    is_revoked = fields.Boolean('已撤销', default=False, index=True)
    revoked_at = fields.Datetime('撤销时间', readonly=True)

    scope = fields.Char('权限范围', default='user')

    # 设备信息（用于安全审计）
    device_info = fields.Text('设备信息')
    ip_address = fields.Char('IP 地址')

    @api.depends('access_token', 'refresh_token')
    def _compute_hashes(self):
        for token in self:
            if token.access_token:
                token.access_token_hash = hashlib.sha256(token.access_token.encode()).hexdigest()
            if token.refresh_token:
                token.refresh_token_hash = hashlib.sha256(token.refresh_token.encode()).hexdigest()

    @api.model
    def _generate_token(self):
        """生成 64 位随机 Token"""
        return secrets.token_hex(32)

    def action_revoke(self):
        """撤销 Token"""
        self.write({
            'is_revoked': True,
            'revoked_at': fields.Datetime.now(),
        })

    def is_access_token_valid(self):
        """检查 Access Token 是否有效"""
        self.ensure_one()
        if self.is_revoked:
            return False
        if self.expires_at and fields.Datetime.now() > self.expires_at:
            return False
        return True

    def is_refresh_token_valid(self):
        """检查 Refresh Token 是否有效"""
        self.ensure_one()
        if self.is_revoked:
            return False
        if self.refresh_expires_at and fields.Datetime.now() > self.refresh_expires_at:
            return False
        return True

    def _get_user_info(self):
        """获取关联用户的基本信息"""
        self.ensure_one()
        user = self.user_id.sudo()
        return {
            'uid': user.id,
            'login': user.login,
            'name': user.name,
            'email': user.email,
            'lang': user.lang,
            'tz': user.tz,
            'company_id': user.company_id.id,
            'company_name': user.company_id.name,
        }

    # ========== Token 管理 API ==========

    @api.model
    def _find_by_access_token(self, access_token):
        """通过 Access Token 查找有效的 Token 记录"""
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        token = self.search([
            ('access_token_hash', '=', token_hash),
            ('is_revoked', '=', False),
            ('expires_at', '>', fields.Datetime.now()),
        ], limit=1)
        return token

    @api.model
    def _find_by_refresh_token(self, refresh_token):
        """通过 Refresh Token 查找有效的 Token 记录"""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        token = self.search([
            ('refresh_token_hash', '=', token_hash),
            ('is_revoked', '=', False),
            ('refresh_expires_at', '>', fields.Datetime.now()),
        ], limit=1)
        return token

    @api.model
    def _create_token(self, user_id, client_id, device_info='', ip_address=''):
        """创建新的 Token 对"""
        client = self.env['auth.client'].browse(client_id)
        now = fields.Datetime.now()
        access_expiry = now + timedelta(hours=client.access_token_expiry)
        refresh_expiry = now + timedelta(days=client.refresh_token_expiry)

        token = self.create({
            'user_id': user_id,
            'client_id': client_id,
            'expires_at': access_expiry,
            'refresh_expires_at': refresh_expiry,
            'device_info': device_info,
            'ip_address': ip_address,
        })
        # 显式计算 hash，避免 computed store=True 延迟落库导致查不到
        if token.access_token:
            token.access_token_hash = hashlib.sha256(token.access_token.encode()).hexdigest()
        if token.refresh_token:
            token.refresh_token_hash = hashlib.sha256(token.refresh_token.encode()).hexdigest()
        return token

    @api.model
    def _refresh_token(self, refresh_token, device_info='', ip_address=''):
        """用 Refresh Token 刷新，返回新的 Token 对"""
        old_token = self._find_by_refresh_token(refresh_token)
        if not old_token:
            raise AccessDenied(_('Refresh Token 无效或已过期'))

        # 撤销旧 Token
        old_token.action_revoke()

        # 创建新 Token
        return self._create_token(
            user_id=old_token.user_id.id,
            client_id=old_token.client_id.id,
            device_info=device_info or old_token.device_info,
            ip_address=ip_address or old_token.ip_address,
        )

    @api.model
    def _cleanup_expired_tokens(self):
        """清理过期的 Token（可由定时任务调用）"""
        expired = self.search([
            '|',
            ('expires_at', '<', fields.Datetime.now()),
            ('refresh_expires_at', '<', fields.Datetime.now()),
        ])
        count = len(expired)
        expired.unlink()
        return count
