# -*- coding: utf-8 -*-
"""
学习平台公共工具模块

提供：
- json_response: 统一 JSON 响应
- error_response: 统一错误响应
- api_verify_auth: 统一 API 签名 + Token 认证
- get_user: 多方式用户认证（旧）
- encode_image: Base64 图片编码
- get_json: 安全获取请求 JSON（旧）
- get_client_ip / get_device_info: 工具函数
"""

import json
import time
import hashlib
import base64
import logging
from odoo.http import request, Response
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


def json_response(data=None, message="ok", success=True, error=None, status=200):
    """统一 JSON 响应格式"""
    body = {
        "success": success,
        "message": message,
        "data": data,
    }
    if error:
        body["error"] = str(error)

    return Response(
        json.dumps(body, ensure_ascii=False, default=str),
        status=status,
        content_type="application/json; charset=utf-8",
    )


def error_response(error, status=400):
    """统一错误响应"""
    return json_response(success=False, message=str(error), error=str(error), status=status)


# ==================== 统一 API 签名认证 ====================

def api_verify_auth(require_token=True):
    """统一 API 签名验证 + Token 认证

    解析统一请求格式:
    {
        "header": { clientId, X-Token, X-Timestamp, X-Nonce, X-Sign, 设备信息... },
        "body": { ... 业务参数 ... }
    }

    签名算法: MD5(X-Timestamp + X-Nonce + X-Token(未登录时可为空串) + bodyJSON(没有body参数就是空串) + appSecret)
    时间戳防重放: 5 分钟内有效

    Args:
        require_token: 是否必须校验 Token（登录/刷新接口为 False）

    Returns:
        (header, body, user_or_None)

    Raises:
        ValueError: 签名或 Token 验证失败
    """
    # 1. 解析请求体
    raw_body = request.httprequest.data
    if isinstance(raw_body, bytes):
        raw_body = raw_body.decode('utf-8')
    data = json.loads(raw_body)

    header = data.get('header', {}) or {}
    body = data.get('body', {}) or {}

    client_id = header.get('clientId', '')
    token = header.get('X-Token', '') or ''
    timestamp = header.get('X-Timestamp', '') or ''
    nonce = header.get('X-Nonce', '') or ''
    sign = header.get('X-Sign', '') or ''

    if not timestamp or not nonce or not sign:
        raise ValueError('缺少签名参数 (X-Timestamp/X-Nonce/X-Sign)')

    # 2. 查找客户端（空则使用默认客户端）
    if client_id:
        client = request.env['auth.client'].sudo().search([
            ('client_id', '=', client_id),
            ('active', '=', True),
        ], limit=1)
        if not client:
            raise ValueError('Client ID 无效')
    else:
        client = request.env['auth.client'].sudo()._get_or_create_default_client()  # noqa

    # 3. 验证时间戳（防重放：前后 5 分钟有效）
    try:
        ts = int(timestamp) / 1000.0
    except (ValueError, TypeError):
        raise ValueError('无效的时间戳')
    if abs(time.time() - ts) > 300:
        raise ValueError('请求已过期，请校准设备时间')

    # 4. 计算并验证签名（空 body 时 bodyJSON 为空串）
    body_str = json.dumps(body, separators=(',', ':'), sort_keys=True, ensure_ascii=False) if body else ''
    sign_raw = timestamp + nonce + token + body_str + client.client_secret
    expected_sign = hashlib.md5(sign_raw.encode('utf-8')).hexdigest()

    if sign != expected_sign:
        _logger.warning("签名验证失败: expected=%s, got=%s", expected_sign, sign)
        raise ValueError('签名验证失败')

    # 5. 验证 Token
    user = None
    if require_token:
        if not token:
            raise ValueError('缺少认证 Token')
        token_record = request.env['auth.token'].sudo()._find_by_access_token(token)  # noqa
        if not token_record or token_record.is_revoked:
            raise ValueError('Token 无效或已过期')
        user = token_record.user_id
        request.update_env(user=user.id)

    return header, body, user


def get_user():
    """
    获取当前用户，支持两种认证方式（优先级从高到低）：
    1. Bearer Token  - Android/iOS App（Header: Authorization: Bearer xxx）
    2. Session Cookie - 浏览器 Web 登录
    """
    # 方式1: Bearer Token 认证（多种方式提取）
    access_token = None
    # 尝试 werkzeug authorization 属性
    auth = request.httprequest.authorization
    if auth and auth.type.lower() == 'bearer':
        access_token = auth.token
    # 尝试遍历 headers
    if not access_token:
        for key, val in request.httprequest.headers:
            if key.lower() == 'authorization' and val.lower().startswith('bearer '):
                access_token = val[7:].strip()
                break
    # 尝试原始 WSGI environ
    if not access_token:
        raw = request.httprequest.environ.get('HTTP_AUTHORIZATION', '')
        if raw.lower().startswith('bearer '):
            access_token = raw[7:].strip()

    if access_token:
        token = request.env['auth.token'].sudo()._find_by_access_token(access_token)  # noqa
        if token:
            request.update_env(user=token.user_id.id)
            return token.user_id
        raise AccessDenied('Access Token 无效或已过期')

    # 方式2: Session 认证
    if request.env.user and request.env.user.id != request.env.ref('base.public_user').id:
        return request.env.user

    raise AccessDenied('请先登录')


def encode_image(binary_data):
    """将二进制图片转为 Base64 字符串"""
    if not binary_data:
        return None
    try:
        return base64.b64encode(binary_data).decode("utf-8")
    except (Exception,):
        return None


def get_client_ip():
    """获取客户端 IP"""
    forwarded = request.httprequest.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.httprequest.remote_addr or ''


def get_device_info():
    """从请求头获取设备信息"""
    # 优先取 App 客户端传入的自定义头
    device = request.httprequest.headers.get('X-Device-Info', '')
    if device:
        return device
    # 兜底取 User-Agent（Swagger UI / curl / 浏览器 都会带）
    return request.httprequest.headers.get('User-Agent', '')


def get_json():
    """安全获取请求 JSON 数据（兼容 Swagger UI 等外部调用）"""
    try:
        return request.jsonrequest
    except AttributeError:
        return json.loads(request.httprequest.data or '{}')
