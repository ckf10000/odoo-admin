# -*- coding: utf-8 -*-
"""内容 API"""
import base64

from odoo import http
from odoo.http import request, Response

from .common import json_response, error_response, api_verify_auth, encode_image, serialize_content  # noqa


class LearnContentController(http.Controller):

    @http.route("/api/v1/learn/contents", type="http", auth="public", methods=["POST"], csrf=False)
    def get_contents(self, **kw):  # noqa
        """获取内容列表（分页、筛选）"""
        try:
            header, body, user = api_verify_auth(require_token=True)
            domain = [("state", "=", "published")]
            for k in ("content_type", "grade", "subject"):
                v = body.get(k)
                if v:
                    domain.append((k, "=", v))
            keyword = body.get("keyword")
            if keyword:
                domain.append(("name", "ilike", keyword))
            page = max(1, int(body.get("page", 1)))
            page_size = min(100, max(1, int(body.get("page_size", 20))))
            total = request.env["learn.content"].sudo().search_count(domain)
            contents = request.env["learn.content"].sudo().search(
                domain, offset=(page - 1) * page_size, limit=page_size, order="sequence, id")
            return json_response(data={
                "list": [serialize_content(c) for c in contents],
                "total": total, "page": page, "page_size": page_size,
            })
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/contents/<int:content_id>", type="http", auth="public", methods=["POST"], csrf=False)
    def get_content_detail(self, content_id, **kw):  # noqa
        """获取内容详情"""
        try:
            header, body, user = api_verify_auth(require_token=True)  # noqa
            content = request.env["learn.content"].sudo().browse(content_id)
            if not content.exists():
                return error_response("内容不存在", 404)
            content.increment_view_count()
            data = serialize_content(content, detail=True)
            if content.content_type in ("exam", "workbook"):
                data["questions"] = [{
                    "id": q.id, "sequence": q.sequence, "question_type": q.question_type,
                    "stem": q.stem, "stem_image": encode_image(q.stem_image) if q.stem_image else None,
                    "options": {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d, "E": q.option_e,
                                "F": q.option_f}
                    if q.question_type in ("single_choice", "multi_choice") else None,
                    "score": q.score, "difficulty": q.difficulty,
                } for q in content.question_ids]
            return json_response(data=data)
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/contents/<int:content_id>/document", type="http", auth="public", methods=["POST"],
                csrf=False)
    def get_document(self, content_id, **kw):  # noqa
        """获取教材文档文件（PDF 流）"""
        try:
            header, body, user = api_verify_auth(require_token=True)  # noqa
            content = request.env["learn.content"].sudo().browse(content_id)
            if not content.exists() or not content.document_file:
                return error_response("文档不存在", 404)
            pdf_data = base64.b64decode(content.document_file)
            return Response(pdf_data, headers={
                "Content-Type": "application/pdf",
                "Content-Disposition": f'inline; filename="{content.document_filename or "document.pdf"}"',
            })
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))
