# -*- coding: utf-8 -*-
"""学习进度 API（预留，后续对接学习记录模型）"""
from odoo import http
from odoo.http import request

from .common import json_response, error_response, api_verify_auth  # noqa


class LearnProgressController(http.Controller):

    @http.route("/api/v1/learn/progress/group/<int:group_id>", type="http", auth="public", methods=["POST"],
                csrf=False)
    def group_progress(self, group_id, **kw):  # noqa
        """获取用户在某内容组下的学习进度

        Request Body:
        {
            "header": {...},
            "body": {}
        }

        Response:
        {
            "success": true,
            "data": {
                "group_id": 1,
                "group_name": "Unit 1 单词学习",
                "total_sections": 3,
                "total_items": 50,
                "completed_items": 25,
                "progress_pct": 50.0
            }
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)  # noqa
            Group = request.env["learn.group"].sudo()
            group = Group.browse(group_id)
            if not group.exists():
                return error_response("内容组不存在", status=404)

            total_items = sum(len(sec.line_ids) for sec in group.section_ids)
            completed = 0

            # TODO: 后续对接学习记录模型 learn.study.record 后，
            # 通过查询用户的学习记录来计算 completed_items
            # completed = request.env["learn.study.record"].sudo().search_count([
            #     ("user_id", "=", user.id),
            #     ("group_id", "=", group_id),
            #     ("status", "=", "completed"),
            # ])

            progress_pct = round(completed / total_items * 100, 1) if total_items > 0 else 0.0

            return json_response(data={
                "group_id": group.id,
                "group_name": group.name,
                "total_sections": len(group.section_ids),
                "total_items": total_items,
                "completed_items": completed,
                "progress_pct": progress_pct,
            })

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))
