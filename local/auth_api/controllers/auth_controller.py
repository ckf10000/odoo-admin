# -*- coding: utf-8 -*-
"""
OAuth2.0 认证控制器

提供以下接口：
- POST /api/auth/token        登录获取 Token（Password Grant）
- POST /api/auth/refresh      刷新 Token
- POST /api/auth/revoke       撤销 Token
- GET  /api/auth/userinfo     获取当前用户信息
- POST /api/auth/logout       登出
"""
import logging
from odoo import http, _  # noqa
from odoo.http import request
from odoo.exceptions import AccessDenied
from odoo.addons.web.controllers.utils import ensure_db  # noqa
from odoo.addons.learn_common.common import (  # noqa
    json_response, error_response, get_client_ip, get_device_info, get_json  # noqa
)

_logger = logging.getLogger(__name__)


def _get_bearer_token():
    """多种方式尝试提取 Bearer Token（按优先级）"""
    # 方式1: werkzeug 的 authorization 属性
    auth = request.httprequest.authorization
    if auth and auth.type.lower() == 'bearer' and auth.token:
        return auth.token
    # 方式2: 遍历 headers（兼容大小写）
    for key, val in request.httprequest.headers:
        if key.lower() == 'authorization' and val.lower().startswith('bearer '):
            return val[7:].strip()
    # 方式3: 读原始 WSGI environ
    raw = request.httprequest.environ.get('HTTP_AUTHORIZATION', '')
    if raw.lower().startswith('bearer '):
        return raw[7:].strip()
    return None


def authenticate_bearer():
    """
    从 Authorization: Bearer <token> 头中验证 Token。
    
    使用方法（在其他控制器中）:
        from odoo.addons.auth_api.controllers.auth_controller import authenticate_bearer
        user = authenticate_bearer()
    
    返回: res.users 记录
    失败: 抛出 AccessDenied
    """
    access_token = _get_bearer_token()
    if not access_token:
        raise AccessDenied(_('缺少认证信息，请在 Authorization 头中提供 Bearer Token'))

    token = request.env['auth.token'].sudo()._find_by_access_token(access_token)  # noqa
    if not token:
        _logger.warning("Token 验证失败: %s...", access_token[:10])
        raise AccessDenied(_('Access Token 无效或已过期'))

    # 更新当前请求的用户环境
    user = token.user_id
    request.update_env(user=user.id)
    return user


# ========== OAuth2.0 控制器 ==========

class AuthController(http.Controller):
    """OAuth2.0 认证 API"""

    # ========== 1. 获取 Token（Password Grant） ==========

    @http.route('/api/auth/token', type='json', auth='public', methods=['POST'], csrf=False)
    def token(self, **kw):  # noqa
        """
        OAuth2.0 Password Grant - 用户名密码登录获取 Token
        
        请求体 (JSON):
        {
            "grant_type": "password",       // 固定值
            "client_id": "xxx",             // 客户端 ID
            "username": "admin",            // Odoo 用户名
            "password": "admin123",         // Odoo 密码
            "db": "odoo.learn.dev"          // 可选，数据库名
        }
        
        响应:
        {
            "success": true,
            "data": {
                "access_token": "xxx",
                "token_type": "Bearer",
                "expires_in": 7200,          // 秒
                "refresh_token": "xxx",
                "user": { ... }
            }
        }
        """
        data = get_json()
        grant_type = data.get('grant_type', 'password')

        if grant_type != 'password':
            return error_response('不支持的 grant_type，当前只支持 password', status=400)

        username = data.get('username', '').strip()
        password = data.get('password', '')
        client_id = data.get('client_id', '').strip()
        db = data.get('db')

        if not username or not password:
            return error_response('用户名和密码不能为空', status=400)

        ip = get_client_ip()
        device_info = get_device_info()

        try:
            # 1. 验证 Client
            if client_id:
                client = request.env['auth.client'].sudo().search([
                    ('client_id', '=', client_id),
                    ('active', '=', True),
                ], limit=1)
                if not client:
                    return error_response('Client ID 无效', status=401)
            else:
                # 使用默认客户端
                client = request.env['auth.client'].sudo()._get_or_create_default_client()  # noqa

            # 2. 指定数据库
            if db:
                ensure_db(db=db)

            # 3. 验证用户名密码
            uid = request.session.authenticate(
                request.env.cr.dbname,
                username,
                password
            )
            if not uid:
                request.env['auth.log'].sudo().log_action(
                    action='failed',
                    login=username,
                    client_id=client.id,
                    ip_address=ip,
                    device_info=device_info,
                    detail='用户名或密码错误',
                )
                return error_response('用户名或密码错误', status=401)

            # 4. 撤销该用户在此客户端的旧 Token（同一用户同一客户端只保留最新）
            old_tokens = request.env['auth.token'].sudo().search([
                ('user_id', '=', uid),
                ('client_id', '=', client.id),
                ('is_revoked', '=', False),
            ])
            old_tokens.action_revoke()

            # 5. 创建新 Token
            user = request.env['res.users'].browse(uid)  # noqa
            token = request.env['auth.token'].sudo()._create_token(  # noqa
                user_id=uid,
                client_id=client.id,
                device_info=device_info,
                ip_address=ip,
            )

            # 6. 记录登录日志
            request.env['auth.log'].sudo().log_action(
                action='login',
                login=username,
                user_id=uid,
                client_id=client.id,
                ip_address=ip,
                device_info=device_info,
            )

            _logger.info("用户 %s 通过 API 登录成功 (Client: %s)", username, client.name)

            # 6. 返回 Token
            expires_in = client.access_token_expiry * 3600
            return {
                'success': True,
                'message': '登录成功',
                'data': {
                    'access_token': token.access_token,
                    'token_type': 'Bearer',
                    'expires_in': expires_in,
                    'refresh_token': token.refresh_token,
                    'scope': token.scope,
                    'user': token._get_user_info(),  # noqa
                }
            }

        except AccessDenied as e:
            request.env['auth.log'].sudo().log_action(
                action='failed',
                login=username,
                client_id=client.id if 'client' in dir() else None,  # noqa
                ip_address=ip,
                device_info=device_info,
                detail=str(e),
            )
            return error_response(str(e), status=401)
        except Exception as e:
            _logger.exception("登录异常: %s", e)
            return error_response(f'服务器内部错误: {e}', status=500)

    # ========== 2. 刷新 Token ==========

    @http.route('/api/auth/refresh', type='json', auth='public', methods=['POST'], csrf=False)
    def refresh(self, **kw):  # noqa
        """
        OAuth2.0 Refresh Token - 用 Refresh Token 获取新的 Token 对
        
        请求体 (JSON):
        {
            "grant_type": "refresh_token",
            "refresh_token": "xxx",
            "client_id": "xxx",            // 客户端 ID
            "client_secret": "xxx"         // 客户端密钥，用于验证客户端身份
        }
        """
        data = get_json()
        grant_type = data.get('grant_type', 'refresh_token')

        if grant_type != 'refresh_token':
            return error_response('不支持的 grant_type', status=400)

        refresh_token = data.get('refresh_token', '').strip()
        if not refresh_token:
            return error_response('Refresh Token 不能为空', status=400)

        client_id = data.get('client_id', '').strip()
        client_secret = data.get('client_secret', '').strip()

        ip = get_client_ip()
        device_info = get_device_info()

        try:
            # 1. 验证客户端身份（client_id + client_secret 必须都传）
            if not client_id:
                return error_response('Client ID 不能为空', status=400)
            if not client_secret:
                return error_response('Client Secret 不能为空', status=400)

            client = request.env['auth.client'].sudo().search([
                ('client_id', '=', client_id),
                ('active', '=', True),
            ], limit=1)
            if not client:
                return error_response('Client ID 无效', status=401)
            if client.client_secret != client_secret:
                return error_response('Client Secret 不匹配', status=401)

            # 2. 刷新 Token
            token = request.env['auth.token'].sudo()._refresh_token(  # noqa
                refresh_token,
                device_info=device_info,
                ip_address=ip,
            )

            # 记录刷新日志
            request.env['auth.log'].sudo().log_action(
                action='refresh',
                login=token.user_id.login,
                user_id=token.user_id.id,
                client_id=token.client_id.id,
                ip_address=ip,
                device_info=device_info,
            )

            client = token.client_id
            expires_in = client.access_token_expiry * 3600

            return {
                'success': True,
                'message': 'Token 刷新成功',
                'data': {
                    'access_token': token.access_token,
                    'token_type': 'Bearer',
                    'expires_in': expires_in,
                    'refresh_token': token.refresh_token,
                    'scope': token.scope,
                }
            }

        except AccessDenied as e:
            return error_response(str(e), status=401)
        except Exception as e:
            _logger.exception("Token 刷新异常: %s", e)
            return error_response(f'服务器内部错误: {e}', status=500)

    # ========== 3. 撤销 Token ==========

    @http.route('/api/auth/revoke', type='json', auth='public', methods=['POST'], csrf=False)
    def revoke(self, **kw):  # noqa
        """
        撤销 Token（登出）
        
        请求体:
        {
            "token": "xxx",              // access_token 或 refresh_token
            "token_type_hint": "access_token"  // 可选
        }
        """
        data = get_json()
        token_str = data.get('token', '').strip()

        if not token_str:
            return error_response('Token 不能为空', status=400)

        try:
            # 尝试作为 access_token 查找
            token = request.env['auth.token'].sudo()._find_by_access_token(token_str)  # noqa
            if not token:
                # 尝试作为 refresh_token 查找
                token = request.env['auth.token'].sudo()._find_by_refresh_token(token_str)  # noqa

            if token and not token.is_revoked:
                token.action_revoke()
                request.env['auth.log'].sudo().log_action(
                    action='revoke',
                    login=token.user_id.login,
                    user_id=token.user_id.id,
                    client_id=token.client_id.id,
                    ip_address=get_client_ip(),
                    device_info=get_device_info(),
                )

            # 即使 token 不存在也返回成功（OAuth2 规范）
            return {'success': True, 'message': 'Token 已撤销'}

        except Exception as e:
            _logger.exception("Token 撤销异常: %s", e)
            return error_response(str(e), status=500)

    # ========== 4. 获取用户信息 ==========

    @http.route('/api/auth/userinfo', type='json', auth='public', methods=['GET', 'POST'], csrf=False)
    def userinfo(self, **kw):  # noqa
        """
        获取当前 Token 对应的用户信息
        
        Header:
        Authorization: Bearer <access_token>
        """
        try:
            user = authenticate_bearer()
            return {
                'success': True,
                'data': {
                    'uid': user.id,
                    'login': user.login,
                    'name': user.name,
                    'email': user.email,
                    'lang': user.lang,
                    'tz': user.tz,
                    'company_id': user.company_id.id,
                    'company_name': user.company_id.name,
                    'groups': user.groups_id.mapped('name'),
                }
            }
        except AccessDenied as e:
            return error_response(str(e), status=401)

    # ========== 5. 登出 ==========

    @http.route('/api/auth/logout', type='json', auth='public', methods=['POST'], csrf=False)
    def logout(self, **kw):  # noqa
        """
        登出 - 撤销当前 Bearer Token
        
        Header:
        Authorization: Bearer <access_token>
        """
        access_token = _get_bearer_token()
        if not access_token:
            return {'success': False, 'message': '请提供 Bearer Token', 'error': '请提供 Bearer Token', 'data': None}
        token = request.env['auth.token'].sudo()._find_by_access_token(access_token)  # noqa

        if token and not token.is_revoked:
            token.action_revoke()
            request.env['auth.log'].sudo().log_action(
                action='revoke',
                login=token.user_id.login,
                user_id=token.user_id.id,
                client_id=token.client_id.id,
                ip_address=get_client_ip(),
                device_info=get_device_info(),
            )

        return {'success': True, 'message': '已登出'}
