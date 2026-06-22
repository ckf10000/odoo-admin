# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

"""学习平台 Web Controller - 前端页面渲染"""


class LearnWebController(http.Controller):

    @http.route("/learn/content/<int:content_id>", type="http", auth="user", website=True)
    def content_detail_page(self, content_id, **kwargs):  # noqa
        """内容详情页面 - 教材阅读/视频观看"""
        content = request.env["learn.content"].sudo().browse(content_id)
        if not content.exists():
            return request.not_found()

        content.increment_view_count()

        # 获取用户交互数据
        user = request.env.user
        is_favorited = request.env["learn.favorite"].sudo().search_count([
            ("user_id", "=", user.id),
            ("content_id", "=", content.id),
        ]) > 0

        user_annotations = request.env["learn.annotation"].sudo().search([
            ("user_id", "=", user.id),
            ("content_id", "=", content.id),
        ], order="page_number")

        user_notes = request.env["learn.note"].sudo().search([
            ("user_id", "=", user.id),
            ("content_id", "=", content.id),
        ], order="create_date desc")

        ratings = request.env["learn.rating"].sudo().search([
            ("content_id", "=", content.id),
            ("is_approved", "=", True),
        ], order="create_date desc", limit=20)

        return request.render("learn_core.content_detail_template", {
            "content": content,
            "is_favorited": is_favorited,
            "annotations": user_annotations,
            "notes": user_notes,
            "ratings": ratings,
        })

    @http.route("/learn/exam/<int:session_id>", type="http", auth="user", website=True)
    def exam_page(self, session_id, **kwargs):  # noqa
        """答题页面"""
        session = request.env["learn.exam.session"].sudo().browse(session_id)
        if not session.exists():
            return request.not_found()

        if session.user_id.id != request.env.user.id:
            return request.render("learn_core.access_denied_template")

        return request.render("learn_core.exam_template", {
            "session": session,
            "answers": session.answer_ids,
        })
