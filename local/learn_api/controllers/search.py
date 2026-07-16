# -*- coding: utf-8 -*-
"""全局搜索 API"""
from odoo import http
from odoo.http import request

from .common import json_response, error_response, api_verify_auth, encode_image  # noqa


class LearnSearchController(http.Controller):

    @http.route("/api/v1/learn/search", type="http", auth="public", methods=["POST"], csrf=False)
    def search(self, **kw):  # noqa
        """全局搜索

        Request Body:
        {
            "header": {...},
            "body": {
                "keyword": "apple",          // 必填，搜索关键词
                "scope": "all",              // 可选：word / character / question / content / all，默认 all
                "page": 1,                   // 可选，页码
                "page_size": 20              // 可选，每页数量
            }
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)
            keyword = body.get("keyword", "").strip()
            if not keyword:
                return error_response("keyword 不能为空", status=400)

            scope = body.get("scope", "all").strip()
            page_size = min(50, max(1, int(body.get("page_size", 20))))

            results = {}

            # ---- 搜索单词 ----
            if scope in ("all", "word"):
                words = request.env["learn.word"].sudo().search([
                    "|", ("name", "ilike", keyword),
                    ("meaning", "ilike", keyword),
                ], order="sequence, id", limit=page_size)
                results["words"] = [{
                    "id": w.id, "name": w.name,
                    "phonetic": w.phonetic or "", "meaning": w.meaning or "",
                    "difficulty": w.difficulty,
                    "pos": [{"id": p.id, "name": p.name, "code": p.code} for p in w.pos_ids],
                } for w in words]

            # ---- 搜索生字 ----
            if scope in ("all", "character"):
                chars = request.env["learn.character"].sudo().search([
                    "|", ("name", "ilike", keyword),
                    ("meaning", "ilike", keyword),
                ], order="sequence, id", limit=page_size)
                results["characters"] = [{
                    "id": ch.id, "name": ch.name,
                    "pinyin": ch.pinyin or "", "meaning": ch.meaning or "",
                    "strokes": ch.strokes or 0, "radical": ch.radical or "",
                    "difficulty": ch.difficulty,
                } for ch in chars]

            # ---- 搜索题目 ----
            if scope in ("all", "question"):
                questions = request.env["learn.question"].sudo().search([
                    ("stem", "ilike", keyword),
                ], order="id", limit=page_size)
                results["questions"] = [{
                    "id": q.id, "question_type": q.question_type,
                    "stem": q.stem or "", "difficulty": q.difficulty,
                } for q in questions]

            # ---- 搜索内容（教材/试卷等） ----
            if scope in ("all", "content"):
                contents = request.env["learn.content"].sudo().search([
                    ("name", "ilike", keyword),
                    ("state", "=", "published"),
                ], order="sequence, id", limit=page_size)
                results["contents"] = [{
                    "id": c.id, "name": c.name,
                    "content_type": c.content_type,
                    "subject": c.subject or "", "grade": c.grade or "",
                    "cover_image": encode_image(c.cover_image),
                } for c in contents]

            return json_response(data={"keyword": keyword, "results": results})

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))
