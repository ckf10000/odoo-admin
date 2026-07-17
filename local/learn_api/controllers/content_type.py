# -*- coding: utf-8 -*-
"""内容类型 API"""
from odoo import http
from odoo.http import request

from .common import json_response, error_response, api_verify_auth  # noqa


class LearnContentTypeController(http.Controller):

    @http.route("/api/v1/learn/content_types", type="http", auth="public", methods=["POST"], csrf=False)
    def get_content_types(self, **kw):  # noqa
        """获取所有启用的内容类型

        Request Body:
        {
            "header": { "clientId": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {}
        }

        Response Body:
        {
            "success": true,
            "data": [
                {
                    "id": 1,
                    "name": "单词卡片",
                    "code": "word_card",
                    "storage_model": "learn.phrase",
                    "has_score": false,
                    "sequence": 10,
                    "description": "查看单词音标、释义、例句、词性"
                },
                {
                    "id": 4,
                    "name": "单选题",
                    "code": "single_choice",
                    "storage_model": "learn.question",
                    "has_score": true,
                    "sequence": 40,
                    "description": "四选一，单选正确答案"
                }
            ]
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)  # noqa
            ctx_lang = user.lang or request.env.context.get('lang', 'zh_CN')
            types = request.env['learn.content.type'].sudo().with_context(lang=ctx_lang).search(
                [('active', '=', True)], order='sequence, id')
            return json_response(data=[{
                "id": t.id,
                "name": t.name,
                "code": t.code,
                "storage_model": t.storage_model,
                "has_score": t.has_score,
                "sequence": t.sequence,
                "description": t.description or "",
            } for t in types])
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))
