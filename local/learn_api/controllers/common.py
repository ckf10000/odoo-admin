# -*- coding: utf-8 -*-
"""公共工具：常量、导入、辅助函数"""
from odoo import fields
from odoo.http import request
from odoo.addons.learn_core.utils import DIM_CHAIN  # noqa
from odoo.addons.common_lib.common import json_response, error_response, api_verify_auth, encode_image  # noqa

ALL_TAB = (0, "all", "全部")  # 全部 Tab: (id, code, name)


def serialize_content(content, detail=False):
    """序列化 content 对象"""
    data = {
        "id": content.id,
        "name": content.name,
        "content_type": content.content_type,
        "subject": content.subject,
        "grade": content.grade,
        "semester": content.semester,
        "publisher": content.publisher,
        "author": content.author,
        "description": content.description,
        "view_count": content.view_count,
        "favorite_count": content.favorite_count,
        "avg_rating": content.avg_rating,
        "state": content.state,
        "tags": [{"id": t.id, "name": t.name} for t in content.tags],
    }
    if detail:
        data.update({
            "isbn": content.isbn,
            "edition": content.edition,
            "cover_image": encode_image(content.cover_image),
            "has_document": bool(content.document_file),
            "video_url": content.video_url,
            "video_platform": content.video_platform,
            "video_duration": content.video_duration,
        })
        if content.content_type in ("exam", "workbook"):
            data.update({
                "total_score": content.total_score,
                "pass_score": content.pass_score,
                "time_limit": content.time_limit,
                "question_count": content.question_count,
            })
    return data


def sync_wrong_book(session):
    """同步错题本"""
    for answer in session.answer_ids:
        if not answer.is_correct:
            existing = request.env["learn.wrong.book"].sudo().search([
                ("user_id", "=", session.user_id.id),
                ("question_id", "=", answer.question_id.id),
            ], limit=1)
            if existing:
                existing.write({
                    "wrong_count": existing.wrong_count + 1,
                    "last_wrong_time": fields.Datetime.now(),
                })
            else:
                request.env["learn.wrong.book"].sudo().create({
                    "user_id": session.user_id.id,
                    "question_id": answer.question_id.id,
                    "wrong_count": 1,
                })
