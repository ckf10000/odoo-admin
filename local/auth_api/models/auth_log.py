# -*- coding: utf-8 -*-
"""
认证日志模型

记录所有认证相关操作：登录、Token 刷新、Token 撤销、登录失败等。
"""
from odoo import models, fields, api


class AuthLog(models.Model):
    """认证日志"""
    _name = 'auth.log'
    _description = 'Authentication Log'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', string='用户', index=True, ondelete='set null')
    client_id = fields.Many2one('auth.client', string='客户端', index=True, ondelete='set null')

    action = fields.Selection([
        ('login', '登录'),
        ('refresh', '刷新 Token'),
        ('revoke', '撤销 Token'),
        ('failed', '登录失败'),
    ], string='操作类型', required=True, index=True)

    login = fields.Char('登录名', help="登录失败时记录尝试的用户名")
    ip_address = fields.Char('IP 地址')
    device_info = fields.Text('设备信息')
    detail = fields.Text('详情')

    @api.model
    def log_action(self, action, user_id=None, client_id=None, login=None, ip_address='', device_info='', detail=''):
        """记录一条认证日志"""
        return self.create({
            'action': action,
            'user_id': user_id,
            'client_id': client_id,
            'login': login,
            'ip_address': ip_address,
            'device_info': device_info,
            'detail': detail,
        })
