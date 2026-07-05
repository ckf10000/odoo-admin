# -*- coding: utf-8 -*-
"""
OAuth2.0 认证控制器

提供以下接口：
- POST /api/v1/auth/token             登录获取 Token（Password Grant）
- POST /api/v1/auth/refresh           刷新 Token
- POST /api/v1/auth/revoke            撤销 Token
- POST /api/v1/auth/userinfo          获取当前用户信息
- POST /api/v1/auth/logout            登出
- POST /api/v1/auth/change-password   修改密码
"""
import json
import logging
from odoo import http, _  # noqa
from odoo.http import request
from odoo.exceptions import AccessDenied
from odoo.addons.web.controllers.utils import ensure_db  # noqa
from odoo.addons.learn_common.common import (  # noqa
    json_response, error_response, api_verify_auth, get_client_ip, get_json  # noqa
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

    @http.route('/api/v1/auth/token', type="http", auth='public', methods=['POST'], csrf=False)
    def token(self, **kw):  # noqa
        """
        OAuth2.0 Password Grant - 用户名密码登录获取 Token

        请求体 (JSON):
        {
            "header": {
                "clientId": "string",      // 客户端ID
                "X-Timestamp": "1720000000000",  // 毫秒时间戳
                "X-Nonce": "uuid",         // 随机UUID
                "X-Sign": "md5"            // 签名（见签名算法文档）
            },
            "body": {
                "username": "admin",       // Odoo 用户名
                "password": "admin123",    // Odoo 密码
                "tenant": "odoo.learn.dev" // 可选，数据库名
            }
        }

        响应:
        {
            "success": true,
            "data": {
                "access_token": "xxx",
                "token_type": "Bearer",
                "expires_in": 7200,
                "refresh_token": "xxx",
                "user": { ... }
            }
        }
        """
        try:
            header, body, _user = api_verify_auth(require_token=False)

            username = body.get('username', '').strip()
            password = body.get('password', '')
            tenant = body.get('tenant')
            client_id = header.get('clientId', '')

            if not username or not password:
                return error_response('用户名和密码不能为空', status=400)

            ip = get_client_ip()

            try:
                # 1. 验证 Client（已在 api_verify_auth 中校验）
                client = request.env['auth.client'].sudo().search([
                    ('client_id', '=', client_id),
                    ('active', '=', True),
                ], limit=1)

                # 2. 指定数据库
                if tenant:
                    ensure_db(db=tenant)

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
                        device_info=json.dumps(header, ensure_ascii=False),
                        detail='用户名或密码错误',
                    )
                    return error_response('用户名或密码错误', status=401)

                # 4. 撤销该用户在此客户端的旧 Token
                old_tokens = request.env['auth.token'].sudo().search([
                    ('user_id', '=', uid),
                    ('client_id', '=', client.id),
                    ('is_revoked', '=', False),
                ])
                old_tokens.action_revoke()

                # 5. 创建新 Token
                user = request.env['res.users'].browse(uid)  # noqa
                header_json = json.dumps(header, ensure_ascii=False)
                token = request.env['auth.token'].sudo()._create_token(  # noqa
                    user_id=uid,
                    client_id=client.id,
                    device_info=header_json,
                    ip_address=ip,
                    header_data=header_json,
                )

                # 6. 记录登录日志
                request.env['auth.log'].sudo().log_action(
                    action='login',
                    login=username,
                    user_id=uid,
                    client_id=client.id,
                    ip_address=ip,
                    device_info=json.dumps(header, ensure_ascii=False),
                )

                _logger.info("用户 %s 通过 API 登录成功 (Client: %s)", username, client.name)

                # 7. 返回 Token
                expires_in = client.access_token_expiry * 3600
                return json_response(data={
                    'access_token': token.access_token,
                    'token_type': 'Bearer',
                    'expires_in': expires_in,
                    'refresh_token': token.refresh_token,
                    'scope': token.scope,
                    'user': token._get_user_info(),  # noqa
                }, message='登录成功')

            except AccessDenied as e:
                request.env['auth.log'].sudo().log_action(
                    action='failed',
                    login=username,
                    client_id=client.id if 'client' in dir() else None,  # noqa
                    ip_address=ip,
                    device_info=json.dumps(header, ensure_ascii=False),
                    detail=str(e),
                )
                return error_response(str(e), status=401)
            except Exception as e:
                _logger.exception("登录异常: %s", e)
                return error_response(f'服务器内部错误: {e}', status=500)

        except ValueError as e:
            _logger.warning("认证失败: %s", e)
            return error_response(str(e), status=401)

    # ========== 2. 刷新 Token ==========

    @http.route('/api/v1/auth/refresh', type="http", auth='public', methods=['POST'], csrf=False)
    def refresh(self, **kw):  # noqa
        """
        OAuth2.0 Refresh Token - 用 Refresh Token 获取新的 Token 对

        请求体 (JSON):
        {
            "header": { "clientId": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {
                "grant_type": "refresh_token",  // 固定值
                "refresh_token": "xxx"           // 登录返回的 refresh_token
            }
        }
        """
        try:
            header, body, _user = api_verify_auth(require_token=False)

            grant_type = body.get('grant_type', 'refresh_token')
            if grant_type != 'refresh_token':
                return error_response('不支持的 grant_type', status=400)

            refresh_token = body.get('refresh_token', '').strip()
            if not refresh_token:
                return error_response('Refresh Token 不能为空', status=400)

            ip = get_client_ip()

            try:
                # 刷新 Token（Client 身份已由签名验证）
                header_json = json.dumps(header, ensure_ascii=False)
                token = request.env['auth.token'].sudo()._refresh_token(  # noqa
                    refresh_token,
                    device_info=header_json,
                    ip_address=ip,
                    header_data=header_json,
                )

                request.env['auth.log'].sudo().log_action(
                    action='refresh',
                    login=token.user_id.login,
                    user_id=token.user_id.id,
                    client_id=token.client_id.id,
                    ip_address=ip,
                    device_info=json.dumps(header, ensure_ascii=False),
                )

                client = token.client_id
                expires_in = client.access_token_expiry * 3600

                return json_response(data={
                    'access_token': token.access_token,
                    'token_type': 'Bearer',
                    'expires_in': expires_in,
                    'refresh_token': token.refresh_token,
                    'scope': token.scope,
                }, message='Token 刷新成功')

            except AccessDenied as e:
                return error_response(str(e), status=401)
            except Exception as e:
                _logger.exception("Token 刷新异常: %s", e)
                return error_response(f'服务器内部错误: {e}', status=500)

        except ValueError as e:
            _logger.warning("认证失败: %s", e)
            return error_response(str(e), status=401)

    # ========== 3. 撤销 Token ==========

    @http.route('/api/v1/auth/revoke', type="http", auth='public', methods=['POST'], csrf=False)
    def revoke(self, **kw):  # noqa
        """
        撤销 Token

        请求体 (JSON):
        {
            "header": { "clientId": "xxx", "X-Token": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {
                "token": "xxx",                        // 要撤销的 token
                "token_type_hint": "access_token"       // 可选
            }
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)

            token_str = body.get('token', '').strip()
            if not token_str:
                return error_response('Token 不能为空', status=400)

            try:
                token = request.env['auth.token'].sudo()._find_by_access_token(token_str)  # noqa
                if not token:
                    token = request.env['auth.token'].sudo()._find_by_refresh_token(token_str)  # noqa

                if token and not token.is_revoked:
                    token.action_revoke()
                    request.env['auth.log'].sudo().log_action(
                        action='revoke',
                        login=token.user_id.login,
                        user_id=token.user_id.id,
                        client_id=token.client_id.id,
                        ip_address=get_client_ip(),
                        device_info=json.dumps(header, ensure_ascii=False),
                    )

                return json_response(message='Token 已撤销')

            except Exception as e:
                _logger.exception("Token 撤销异常: %s", e)
                return error_response(str(e), status=500)

        except ValueError as e:
            _logger.warning("认证失败: %s", e)
            return error_response(str(e), status=401)

    # ========== 4. 获取用户信息 ==========

    @http.route('/api/v1/auth/userinfo', type="http", auth='public', methods=['POST'], csrf=False)
    def userinfo(self, **kw):  # noqa
        """
        获取当前 Token 对应的用户信息

        请求体 (JSON):
        {
            "header": { "clientId": "xxx", "X-Token": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {}
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)

            return json_response(data={
                'uid': user.id,
                'login': user.login,
                'name': user.name,
                'email': user.email,
                'lang': user.lang,
                'tz': user.tz,
                'company_id': user.company_id.id,
                'company_name': user.company_id.name,
                'groups': user.groups_id.mapped('name'),
            })

        except ValueError as e:
            _logger.warning("认证失败: %s", e)
            return error_response(str(e), status=401)

    # ========== 5. 登出 ==========

    @http.route('/api/v1/auth/logout', type="http", auth='public', methods=['POST'], csrf=False)
    def logout(self, **kw):  # noqa
        """
        登出 - 撤销当前 Token

        请求体 (JSON):
        {
            "header": { "clientId": "xxx", "X-Token": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {}
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)

            token = request.env['auth.token'].sudo()._find_by_access_token(  # noqa
                header.get('X-Token', '')
            )

            if token and not token.is_revoked:
                # 更新最新的 header 信息
                header_json = json.dumps(header, ensure_ascii=False)
                token.write({
                    'header_data': header_json,
                    'device_info': header_json,
                    'ip_address': get_client_ip(),
                })
                token.action_revoke()
                request.env['auth.log'].sudo().log_action(
                    action='revoke',
                    login=token.user_id.login,
                    user_id=token.user_id.id,
                    client_id=token.client_id.id,
                    ip_address=get_client_ip(),
                    device_info=header_json,
                )

            return json_response(message='已登出')

        except ValueError as e:
            _logger.warning("认证失败: %s", e)
            return error_response(str(e), status=401)

    # ========== 6. 修改密码 ==========

    @http.route('/api/v1/auth/change-password', type="http", auth='public', methods=['POST'], csrf=False)
    def change_password(self, **kw):  # noqa
        """
        修改当前用户密码

        请求体 (JSON):
        {
            "header": { "clientId": "xxx", "X-Token": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {
                "old_password": "当前密码",
                "new_password": "新密码"        // 长度 >= 6
            }
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)

            old_password = body.get('old_password', '')
            new_password = body.get('new_password', '')

            # 参数校验
            if not old_password:
                return error_response('旧密码不能为空', status=400)
            if not new_password:
                return error_response('新密码不能为空', status=400)
            if len(new_password) < 6:
                return error_response('新密码长度不能少于6位', status=400)
            if old_password == new_password:
                return error_response('新密码不能与旧密码相同', status=400)

            # 用 Odoo 原生 authenticate 校验旧密码（与登录逻辑一致）
            try:
                uid = request.session.authenticate(
                    request.env.cr.dbname, user.login, old_password
                )
            except AccessDenied:
                uid = None
            if not uid:
                _logger.warning("用户 %s 修改密码失败: 旧密码不正确", user.login)
                return error_response('旧密码不正确', status=400)

            user.sudo().write({'password': new_password})

            # 密码修改成功后，撤销该用户所有有效 Token（强制重新登录）
            active_tokens = request.env['auth.token'].sudo().search([
                ('user_id', '=', user.id),
                ('is_revoked', '=', False),
            ])
            revoked_count = len(active_tokens)
            active_tokens.action_revoke()

            # 记录日志
            ip = get_client_ip()
            request.env['auth.log'].sudo().log_action(
                action='change_password',
                login=user.login,
                user_id=user.id,
                ip_address=ip,
                device_info=json.dumps(header, ensure_ascii=False),
                detail=f'用户通过 Android API 修改密码，已撤销 {revoked_count} 个有效 Token',
            )

            _logger.info("用户 %s 密码修改成功", user.login)
            return json_response(message='密码修改成功')

        except ValueError as e:
            _logger.warning("认证失败: %s", e)
            return error_response(str(e), status=401)
        except AccessDenied as e:
            _logger.warning("拒绝访问: %s", e)
            return error_response(str(e), status=401)
        except Exception as e:
            _logger.exception("修改密码异常: %s", e)
            return error_response(str(e), status=500)
