# -*- coding: utf-8 -*-
"""选择器-过程 API"""
from odoo import http
from odoo.http import request

from .common import json_response, error_response, api_verify_auth  # noqa


class LearnSelectorProcessController(http.Controller):

    @http.route("/api/v1/learn/selector_processes", type="http", auth="public", methods=["POST"], csrf=False)
    def get_selector_processes(self, **kw):  # noqa
        """查询 selector 下绑定的过程列表，排序后第一个过程附带其内容组（分页）

        Request Body:
        {
            "header": {
                "clientId": "xxx", // 客户端ID
                "X-Token": "xxx",  // 认证 Token
                "X-Timestamp": "...", // 时间戳
                "X-Nonce": "...",    // 随机串
                "X-Sign": "..."      // 签名
            },
            "body": {
                "selector_code": "CHILDREN_BEGINNER_AGE_6_TEEN_2025_S1_PHONICS_LESSON", // selector 的 code
                "page_num": 1,        // 可选，页码，默认 1
                "page_size": 10   // 可选，每页数量，默认 10
            }
        }

        Response Body(JSON):
        {
            "success": true,
            "data":  [
                {
                    "id": 1,
                    "process_id": 1,
                    "process_name": "单词基础",
                    "process_code": "WORD_BASIC",
                    "sequence": 10,
                    "groups": {
                        "list": [
                            {
                                "id": 1,
                                "name": "CASE FILE 01",
                                "sequence": 10,
                                "item_count": 100
                                "content_type": "word",
                                "content_type_id": 1
                            }
                        ],
                        "total": 1,
                        "page_num": 1,
                        "page_size": 10
                    }
                },
                {
                    "id": 2,
                    "process_id": 2,
                    "process_name": "默写专项",
                    "process_code": "WRITING_SPECIAL",
                    "sequence": 20,
                    "groups": null
                }
            ]
        """
        try:
            header, body, user = api_verify_auth(require_token=True)  # noqa
            selector_code = body.get("selector_code")
            if not selector_code:
                return error_response("selector_code 不能为空", status=400)

            page_num = max(1, int(body.get("page_num", 1)))
            page_size = min(50, max(1, int(body.get("page_size", 10))))
            ctx_lang = user.lang or request.env.context.get('lang', 'zh_CN')

            Selector = request.env['learn.selector'].sudo().with_context(lang=ctx_lang)
            SP = request.env['learn.selector.process'].sudo().with_context(lang=ctx_lang)
            Group = request.env['learn.group'].sudo().with_context(lang=ctx_lang)

            sel = Selector.search([('code', '=', selector_code)], limit=1)
            if not sel:
                return error_response("选择器不存在", status=404)

            sp_records = SP.search([('selector_id', '=', sel.id)], order='sequence, id')

            processes = []
            for i, sp in enumerate(sp_records):
                item = {
                    "id": sp.id,
                    "process_id": sp.process_id.id,
                    "process_name": sp.process_id.name,
                    "process_code": sp.process_id.code,
                    "sequence": sp.sequence,
                    "groups": None,
                }
                if i == 0:
                    offset = (page_num - 1) * page_size
                    total = Group.search_count([('selector_process_id', '=', sp.id)])
                    groups = Group.search(
                        [('selector_process_id', '=', sp.id)],
                        offset=offset, limit=page_size, order='sequence, id')
                    item["groups"] = {
                        "list": [{
                            "id": g.id,
                            "name": g.name,
                            "sequence": g.sequence,
                            "content_type": g.content_type,
                            "content_type_id": g.content_type_id.id,
                            "item_count": len(g.line_ids),
                        } for g in groups],
                        "total": total, "page_num": page_num, "page_size": page_size,
                    }
                processes.append(item)

            return json_response(data=processes)
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))
