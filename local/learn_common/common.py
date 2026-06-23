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
    # 方式1: Bearer Token 认证
    auth_header = request.httprequest.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        access_token = auth_header[7:].strip()
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
