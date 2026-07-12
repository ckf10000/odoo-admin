# -*- coding: utf-8 -*-
"""交互 API：收藏 / 批注 / 笔记 / 评分"""
from odoo import http
from odoo.http import request

from .common import json_response, error_response, api_verify_auth  # noqa


class LearnInteractController(http.Controller):

    # ---- 收藏 ----
    @http.route("/api/v1/learn/favorites", type="http", auth="public", methods=["POST"], csrf=False)
    def get_favorites(self, **kw):  # noqa
        try:
            header, body, user = api_verify_auth(require_token=True)
            favorites = request.env["learn.favorite"].sudo().search([("user_id", "=", user.id)],
                                                                    order="create_date desc")
            return json_response(data=[{
                "id": f.id, "content_id": f.content_id.id, "content_name": f.content_name,
                "content_type": f.content_type, "create_date": str(f.create_date),
            } for f in favorites])
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/favorites/toggle", type="http", auth="public", methods=["POST"], csrf=False)
    def toggle_favorite(self, **kw):  # noqa
        try:
            header, body, user = api_verify_auth(require_token=True)
            existing = request.env["learn.favorite"].sudo().search(
                [("user_id", "=", user.id), ("content_id", "=", body.get("content_id"))], limit=1)
            if existing:
                existing.unlink()
                return json_response(data={"favorited": False}, message="已取消收藏")
            request.env["learn.favorite"].sudo().create({"user_id": user.id, "content_id": body.get("content_id")})
            return json_response(data={"favorited": True}, message="已收藏")
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    # ---- 批注 ----
    @http.route("/api/v1/learn/annotations/list", type="http", auth="public", methods=["POST"], csrf=False)
    def get_annotations(self, **kw):  # noqa
        try:
            header, body, user = api_verify_auth(require_token=True)
            annotations = request.env["learn.annotation"].sudo().search(
                [("user_id", "=", user.id), ("content_id", "=", int(body.get("content_id")))],
                order="page_number, create_date")
            return json_response(data=[{
                "id": a.id, "page_number": a.page_number, "position_x": a.position_x, "position_y": a.position_y,
                "selected_text": a.selected_text, "annotation_type": a.annotation_type,
                "annotation_text": a.annotation_text, "color": a.color,
            } for a in annotations])
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/annotations", type="http", auth="public", methods=["POST"], csrf=False)
    def create_annotation(self, **kw):  # noqa
        try:
            header, body, user = api_verify_auth(require_token=True)
            body["user_id"] = user.id
            annotation = request.env["learn.annotation"].sudo().create(body)
            return json_response(data={"id": annotation.id})
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    # ---- 笔记 ----
    @http.route("/api/v1/learn/notes/list", type="http", auth="public", methods=["POST"], csrf=False)
    def get_notes(self, **kw):  # noqa
        try:
            header, body, user = api_verify_auth(require_token=True)
            domain = [("user_id", "=", user.id)]
            cid = body.get("content_id")
            if cid:
                domain.append(("content_id", "=", int(cid)))
            notes = request.env["learn.note"].sudo().search(domain, order="create_date desc")
            return json_response(data=[{
                "id": n.id, "title": n.title, "content": n.content,
                "content_id": n.content_id.id, "content_name": n.content_id.name,
                "page_number": n.page_number, "is_private": n.is_private, "create_date": str(n.create_date),
            } for n in notes])
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/notes", type="http", auth="public", methods=["POST"], csrf=False)
    def create_note(self, **kw):  # noqa
        try:
            header, body, user = api_verify_auth(require_token=True)
            body["user_id"] = user.id
            nid = body.get("id")
            if nid:
                note = request.env["learn.note"].sudo().browse(nid)
                if note.user_id.id != user.id:
                    return error_response("无权操作", 403)
                note.write(body)
            else:
                note = request.env["learn.note"].sudo().create(body)
            return json_response(data={"id": note.id})
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    # ---- 评分 ----
    @http.route("/api/v1/learn/ratings/list", type="http", auth="public", methods=["POST"], csrf=False)
    def get_ratings(self, **kw):  # noqa
        try:
            header, body, user = api_verify_auth(require_token=True)
            ratings = request.env["learn.rating"].sudo().search(
                [("content_id", "=", int(body.get("content_id"))), ("is_approved", "=", True)],
                order="create_date desc")
            return json_response(data=[{
                "id": r.id, "user_name": r.user_id.name, "score": r.score,
                "comment": r.comment, "create_date": str(r.create_date),
            } for r in ratings])
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/ratings", type="http", auth="public", methods=["POST"], csrf=False)
    def create_rating(self, **kw):  # noqa
        try:
            header, body, user = api_verify_auth(require_token=True)
            existing = request.env["learn.rating"].sudo().search(
                [("user_id", "=", user.id), ("content_id", "=", body.get("content_id"))], limit=1)
            if existing:
                existing.write({"score": body.get("score"), "comment": body.get("comment", "")})
                return json_response(data={"id": existing.id}, message="评价已更新")
            rating = request.env["learn.rating"].sudo().create({
                "user_id": user.id, "content_id": body.get("content_id"),
                "score": body.get("score"), "comment": body.get("comment", ""),
            })
            return json_response(data={"id": rating.id}, message="评价成功")
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))
