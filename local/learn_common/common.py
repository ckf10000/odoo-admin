# -*- coding: utf-8 -*-
"""
学习平台公共工具模块

提供：
- _json_response: 统一 JSON 响应
- _error_response: 统一错误响应
- _get_user: 多方式用户认证
- _encode_image: Base64 图片编码
"""

import json
import base64
from odoo.http import request, Response
from odoo.exceptions import AccessDenied


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
