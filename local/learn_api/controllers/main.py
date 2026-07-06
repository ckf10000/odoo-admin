# -*- coding: utf-8 -*-
"""
学习平台 REST API

接口前缀: /api/v1/learn/

认证方式: 统一请求格式 POST + api_verify_auth

响应格式:
  {
    "success": true/false,
    "data": {...},
    "message": "...",
    "error": "..."  // 仅在失败时
  }
"""
import base64
from odoo import http, fields
from odoo.http import request, Response

from odoo.addons.learn_common.common import json_response, error_response, api_verify_auth, encode_image  # noqa


# ==================== 分类 API ====================

class LearnCategoryController(http.Controller):

    @http.route("/api/v1/learn/categories", type="http", auth="public", methods=["POST"], csrf=False)
    def get_categories(self, **kwargs):  # noqa
        """获取分类列表

        请求体 (JSON):
        {
            "header": { "clientId": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {
                "parent_id": 0,                 // 可选，父分类ID
                "audience_type": "string",       // 可选，受众人群过滤
                "recursive": false,              // 可选，是否递归
                "include_content_count": false   // 可选，是否含数量统计
            }
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)
            domain = []
            parent_id = body.get("parent_id")
            audience_type = body.get("audience_type")
            recursive = body.get("recursive", "false").lower() == "true"
            include_count = body.get("include_content_count", "false").lower() == "true"

            if parent_id:
                domain.append(("parent_id", "=", int(parent_id)))
            else:
                domain.append(("parent_id", "=", False))

            if audience_type:
                domain.append(("audience_type", "=", audience_type))

            categories = request.env["learn.category"].sudo().search(domain, order="sequence")

            result = []
            for cat in categories:
                item = {
                    "id": cat.id,
                    "name": cat.name,
                    "code": cat.code,
                    "level": cat.level,
                    "is_leaf": cat.is_leaf,
                    "audience_type": cat.audience_type,
                    "stage_info": cat.stage_info,
                    "description": cat.description,
                }
                if include_count:
                    item["content_count"] = cat.content_count
                if recursive:
                    item["children"] = _get_children(cat, include_count)
                result.append(item)

            return json_response(data=result)

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/categories/tree", type="http", auth="public", methods=["POST"], csrf=False)
    def get_category_tree(self, **kwargs):  # noqa
        """获取完整分类树（所有层级）

        请求体 (JSON):
        {
            "header": { "clientId": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {
                "audience_type": "string"        // 可选，受众人群过滤
            }
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)
            audience_type = body.get("audience_type")
            domain = [("parent_id", "=", False)]
            if audience_type:
                domain.append(("audience_type", "=", audience_type))

            roots = request.env["learn.category"].sudo().search(domain, order="sequence")
            tree = []
            for root in roots:
                tree.append(_build_tree(root))

            return json_response(data=tree)

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))


# ==================== 内容 API ====================

class LearnContentController(http.Controller):

    @http.route("/api/v1/learn/contents", type="http", auth="public", methods=["POST"], csrf=False)
    def get_contents(self, **kwargs):  # noqa
        """获取内容列表

        请求体 (JSON):
        {
            "header": { "clientId": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {
                "category_id": 0,                // 可选，分类ID
                "content_type": "textbook",      // 可选，内容类型
                "grade": "string",               // 可选，年级
                "subject": "string",             // 可选，科目
                "keyword": "string",             // 可选，搜索关键字
                "page": 1,                       // 可选，页码
                "page_size": 20                  // 可选，每页数量
            }
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)
            domain = [("state", "=", "published")]

            category_id = body.get("category_id")
            if category_id:
                # 包含子分类
                cat = request.env["learn.category"].sudo().browse(int(category_id))
                if cat.exists():
                    all_cats = cat._get_all_child_ids()  # noqa
                    domain.append(("category_id", "in", all_cats))
                else:
                    domain.append(("category_id", "=", int(category_id)))

            content_type = body.get("content_type")
            if content_type:
                domain.append(("content_type", "=", content_type))

            grade = body.get("grade")
            if grade:
                domain.append(("grade", "=", grade))

            subject = body.get("subject")
            if subject:
                domain.append(("subject", "=", subject))

            keyword = body.get("keyword")
            if keyword:
                domain.append(("name", "ilike", keyword))

            # 分页
            page = max(1, int(body.get("page", 1)))
            page_size = min(100, max(1, int(body.get("page_size", 20))))
            offset = (page - 1) * page_size

            total = request.env["learn.content"].sudo().search_count(domain)
            contents = request.env["learn.content"].sudo().search(
                domain, offset=offset, limit=page_size, order="sequence, id",
            )

            result = []
            for c in contents:
                result.append(_serialize_content(c))

            return json_response(data={
                "list": result,
                "total": total,
                "page": page,
                "page_size": page_size,
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

            data = _serialize_content(content, detail=True)

            # 如果是试卷/练习册，返回题目列表
            if content.content_type in ("exam", "workbook"):
                questions = []
                for q in content.question_ids:
                    questions.append({
                        "id": q.id,
                        "sequence": q.sequence,
                        "question_type": q.question_type,
                        "stem": q.stem,
                        "stem_image": encode_image(q.stem_image) if q.stem_image else None,
                        "options": {
                            "A": q.option_a,
                            "B": q.option_b,
                            "C": q.option_c,
                            "D": q.option_d,
                            "E": q.option_e,
                            "F": q.option_f,
                        } if q.question_type in ("single_choice", "multi_choice") else None,
                        "score": q.score,
                        "difficulty": q.difficulty,
                    })
                data["questions"] = questions

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
            return Response(
                pdf_data,
                headers={
                    "Content-Type": "application/pdf",
                    "Content-Disposition": f'inline; filename="{content.document_filename or "document.pdf"}"',
                },
            )

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))


# ==================== 试卷答题 API ====================

class LearnExamController(http.Controller):

    @http.route("/api/v1/learn/exam/start", type="http", auth="public", methods=["POST"], csrf=False)
    def start_exam(self, **kwargs):  # noqa
        """开始答题

        Body (JSON):
            content_id: int - 试卷/练习册 ID
            session_type: str - practice/exam/retry
            source_session_id: int - 错题重练时传原始会话 ID
        """
        try:
            header, body, user = api_verify_auth(require_token=True)
            content_id = body.get("content_id")
            session_type = body.get("session_type", "practice")
            source_session_id = body.get("source_session_id")

            vals = {
                "content_id": content_id,
                "session_type": session_type,
                "user_id": user.id,
            }
            if source_session_id:
                vals["source_session_id"] = source_session_id

            session = request.env["learn.exam.session"].sudo().create(vals)
            session.action_start()

            # 返回答题明细（不含答案）
            answers = []
            for a in session.answer_ids:
                q = a.question_id
                answers.append({
                    "id": a.id,
                    "question_id": q.id,
                    "question_type": q.question_type,
                    "stem": q.stem,
                    "options": {
                        "A": q.option_a,
                        "B": q.option_b,
                        "C": q.option_c,
                        "D": q.option_d,
                        "E": q.option_e,
                        "F": q.option_f,
                    } if q.question_type in ("single_choice", "multi_choice") else None,
                    "score": q.score,
                    "user_answer": None,
                    "is_correct": None,
                })

            return json_response(data={
                "session_id": session.id,
                "content_name": session.content_id.name,
                "total_score": session.content_id.total_score,
                "pass_score": session.content_id.pass_score,
                "time_limit": session.content_id.time_limit,
                "answers": answers,
            })

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/exam/save_answer", type="http", auth="public", methods=["POST"], csrf=False)
    def save_answer(self, **kwargs):  # noqa
        """保存单题答案

        Body (JSON):
            answer_id: int - 答题明细 ID
            user_answer: str - 用户答案
        """
        try:
            header, body, user = api_verify_auth(require_token=True)
            answer_id = body.get("answer_id")
            user_answer = body.get("user_answer", "")

            answer = request.env["learn.exam.answer"].sudo().browse(answer_id)
            if not answer.exists():
                return error_response("答题明细不存在", 404)

            if answer.session_id.user_id.id != user.id:
                return error_response("无权操作", 403)

            answer.write({"user_answer": user_answer})
            return json_response(data={"id": answer.id, "saved": True})

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/exam/submit", type="http", auth="public", methods=["POST"], csrf=False)
    def submit_exam(self, **kwargs):  # noqa
        """提交试卷并自动批阅

        Body (JSON):
            session_id: int - 答题会话 ID
        """
        try:
            header, body, user = api_verify_auth(require_token=True)
            session_id = body.get("session_id")

            session = request.env["learn.exam.session"].sudo().browse(session_id)
            if not session.exists():
                return error_response("会话不存在", 404)

            if session.user_id.id != user.id:
                return error_response("无权操作", 403)

            if session.state != "in_progress":
                return error_response("该会话已提交", 400)

            session.action_submit()
            session.action_review()

            # 同步错题本
            _sync_wrong_book(session)

            # 返回成绩
            return json_response(data={
                "session_id": session.id,
                "total_score": session.total_score,
                "earned_score": session.earned_score,
                "score_percent": session.score_percent,
                "is_passed": session.is_passed,
                "correct_count": session.correct_count,
                "wrong_count": session.wrong_count,
                "total_questions": session.total_questions,
                "duration": session.duration,
                "answers": [{
                    "id": a.id,
                    "question_id": a.question_id.id,
                    "question_type": a.question_id.question_type,
                    "stem": a.question_id.stem,
                    "user_answer": a.user_answer,
                    "correct_answer": a.question_id.correct_answer,
                    "explanation": a.question_id.answer_explanation,
                    "is_correct": a.is_correct,
                    "earned_score": a.earned_score,
                    "score": a.score,
                } for a in session.answer_ids],
            })

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/exam/history", type="http", auth="public", methods=["POST"], csrf=False)
    def exam_history(self, **kwargs):  # noqa
        """成绩历史

        请求体 (JSON):
        {
            "header": { "clientId": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {
                "content_id": 0,                 // 可选，按内容过滤
                "page": 1,                       // 可选，页码
                "page_size": 20                  // 可选，每页数量
            }
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)
            domain = [("user_id", "=", user.id), ("state", "=", "reviewed")]

            content_id = body.get("content_id")
            if content_id:
                domain.append(("content_id", "=", int(content_id)))

            page = max(1, int(body.get("page", 1)))
            page_size = min(100, max(1, int(body.get("page_size", 20))))
            offset = (page - 1) * page_size

            total = request.env["learn.exam.session"].sudo().search_count(domain)
            sessions = request.env["learn.exam.session"].sudo().search(
                domain, offset=offset, limit=page_size, order="create_date desc",
            )

            records = []
            for s in sessions:
                records.append({
                    "id": s.id,
                    "name": s.name,
                    "content_id": s.content_id.id,
                    "content_name": s.content_id.name,
                    "session_type": s.session_type,
                    "total_score": s.total_score,
                    "earned_score": s.earned_score,
                    "score_percent": s.score_percent,
                    "is_passed": s.is_passed,
                    "correct_count": s.correct_count,
                    "wrong_count": s.wrong_count,
                    "total_questions": s.total_questions,
                    "duration": s.duration,
                    "create_date": str(s.create_date),
                })

            return json_response(data={
                "list": records,
                "total": total,
                "page": page,
                "page_size": page_size,
            })

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))


# ==================== 错题本 API ====================

class LearnWrongBookController(http.Controller):

    @http.route("/api/v1/learn/wrong_book", type="http", auth="public", methods=["POST"], csrf=False)
    def get_wrong_book(self, **kwargs):  # noqa
        """获取错题本

        请求体 (JSON):
        {
            "header": { "clientId": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {
                "content_id": 0,                 // 可选，按试卷过滤
                "is_mastered": false,            // 可选，是否已掌握
                "page": 1,                       // 可选，页码
                "page_size": 20                  // 可选，每页数量
            }
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)
            domain = [("user_id", "=", user.id), ("is_mastered", "=", False)]

            content_id = body.get("content_id")
            if content_id:
                domain.append(("content_id", "=", int(content_id)))

            mastered = body.get("is_mastered")
            if mastered is not None:
                domain = [("user_id", "=", user.id),
                          ("is_mastered", "=", mastered.lower() == "true")]

            page = max(1, int(body.get("page", 1)))
            page_size = min(100, max(1, int(body.get("page_size", 20))))
            offset = (page - 1) * page_size

            total = request.env["learn.wrong.book"].sudo().search_count(domain)
            records = request.env["learn.wrong.book"].sudo().search(
                domain, offset=offset, limit=page_size, order="last_wrong_time desc",
            )

            items = []
            for wb in records:
                q = wb.question_id
                items.append({
                    "id": wb.id,
                    "question_id": q.id,
                    "question_type": q.question_type,
                    "stem": q.stem,
                    "correct_answer": q.correct_answer,
                    "explanation": q.answer_explanation,
                    "difficulty": q.difficulty,
                    "content_id": wb.content_id.id,
                    "content_name": wb.content_id.name,
                    "wrong_count": wb.wrong_count,
                    "last_wrong_time": str(wb.last_wrong_time),
                })

            return json_response(data={
                "list": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            })

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/wrong_book/<int:record_id>/mastered", type="http", auth="public", methods=["POST"],
                csrf=False)
    def mark_mastered(self, record_id, **kw):  # noqa
        """标记错题已掌握"""
        try:
            header, body, user = api_verify_auth(require_token=True)
            record = request.env["learn.wrong.book"].sudo().browse(record_id)
            if not record.exists():
                return error_response("记录不存在", 404)
            if record.user_id.id != user.id:
                return error_response("无权操作", 403)

            record.action_mastered()
            return json_response(data={"id": record.id, "is_mastered": True})

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))


# ==================== 收藏/批注/笔记/评论 API ====================

class LearnInteractController(http.Controller):

    # ---- 收藏 ----
    @http.route("/api/v1/learn/favorites", type="http", auth="public", methods=["POST"], csrf=False)
    def get_favorites(self, **kwargs):  # noqa
        """获取收藏列表"""
        try:
            header, body, user = api_verify_auth(require_token=True)
            favorites = request.env["learn.favorite"].sudo().search([
                ("user_id", "=", user.id),
            ], order="create_date desc")

            items = []
            for fav in favorites:
                items.append({
                    "id": fav.id,
                    "content_id": fav.content_id.id,
                    "content_name": fav.content_name,
                    "content_type": fav.content_type,
                    "create_date": str(fav.create_date),
                })

            return json_response(data=items)

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/favorites/toggle", type="http", auth="public", methods=["POST"], csrf=False)
    def toggle_favorite(self, **kwargs):  # noqa
        """切换收藏状态"""
        try:
            header, body, user = api_verify_auth(require_token=True)
            content_id = body.get("content_id")

            existing = request.env["learn.favorite"].sudo().search([
                ("user_id", "=", user.id),
                ("content_id", "=", content_id),
            ], limit=1)

            if existing:
                existing.unlink()
                return json_response(data={"favorited": False}, message="已取消收藏")
            else:
                request.env["learn.favorite"].sudo().create({
                    "user_id": user.id,
                    "content_id": content_id,
                })
                return json_response(data={"favorited": True}, message="已收藏")

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    # ---- 批注 ----
    @http.route("/api/v1/learn/annotations/list", type="http", auth="public", methods=["POST"], csrf=False)
    def get_annotations(self, **kw):  # noqa
        """获取某内容的批注列表"""
        try:
            header, body, user = api_verify_auth(require_token=True)
            content_id = body.get("content_id")
            annotations = request.env["learn.annotation"].sudo().search([
                ("user_id", "=", user.id),
                ("content_id", "=", int(content_id)),
            ], order="page_number, create_date")

            items = []
            for ann in annotations:
                items.append({
                    "id": ann.id,
                    "page_number": ann.page_number,
                    "position_x": ann.position_x,
                    "position_y": ann.position_y,
                    "selected_text": ann.selected_text,
                    "annotation_type": ann.annotation_type,
                    "annotation_text": ann.annotation_text,
                    "color": ann.color,
                })

            return json_response(data=items)

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/annotations", type="http", auth="public", methods=["POST"], csrf=False)
    def create_annotation(self, **kwargs):  # noqa
        """创建批注"""
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
        """获取笔记列表"""
        try:
            header, body, user = api_verify_auth(require_token=True)
            content_id = body.get("content_id")

            domain = [("user_id", "=", user.id)]
            if content_id:
                domain.append(("content_id", "=", int(content_id)))

            notes = request.env["learn.note"].sudo().search(domain, order="create_date desc")

            items = []
            for note in notes:
                items.append({
                    "id": note.id,
                    "title": note.title,
                    "content": note.content,
                    "content_id": note.content_id.id,
                    "content_name": note.content_id.name,
                    "page_number": note.page_number,
                    "is_private": note.is_private,
                    "create_date": str(note.create_date),
                })

            return json_response(data=items)

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/notes", type="http", auth="public", methods=["POST"], csrf=False)
    def create_note(self, **kwargs):  # noqa
        """创建/更新笔记"""
        try:
            header, body, user = api_verify_auth(require_token=True)
            body["user_id"] = user.id

            note_id = body.get("id")
            if note_id:
                note = request.env["learn.note"].sudo().browse(note_id)
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

    # ---- 评分评论 ----
    @http.route("/api/v1/learn/ratings/list", type="http", auth="public", methods=["POST"], csrf=False)
    def get_ratings(self, **kw):  # noqa
        """获取内容评论列表"""
        try:
            header, body, user = api_verify_auth(require_token=True)
            content_id = body.get("content_id")
            ratings = request.env["learn.rating"].sudo().search([
                ("content_id", "=", int(content_id)),
                ("is_approved", "=", True),
            ], order="create_date desc")

            items = []
            for r in ratings:
                items.append({
                    "id": r.id,
                    "user_name": r.user_id.name,
                    "score": r.score,
                    "comment": r.comment,
                    "create_date": str(r.create_date),
                })

            return json_response(data=items)

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/ratings", type="http", auth="public", methods=["POST"], csrf=False)
    def create_rating(self, **kwargs):  # noqa
        """评分/评论"""
        try:
            header, body, user = api_verify_auth(require_token=True)

            existing = request.env["learn.rating"].sudo().search([
                ("user_id", "=", user.id),
                ("content_id", "=", body.get("content_id")),
            ], limit=1)

            if existing:
                existing.write({
                    "score": body.get("score"),
                    "comment": body.get("comment", ""),
                })
                return json_response(data={"id": existing.id}, message="评价已更新")
            else:
                rating = request.env["learn.rating"].sudo().create({
                    "user_id": user.id,
                    "content_id": body.get("content_id"),
                    "score": body.get("score"),
                    "comment": body.get("comment", ""),
                })
                return json_response(data={"id": rating.id}, message="评价成功")

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))


# ==================== 导航 Tab API ====================

class LearnNavController(http.Controller):

    @http.route("/api/v1/learn/nav_tabs", type="http", auth="public", methods=["POST"], csrf=False)
    def get_nav_tabs(self, **kw):  # noqa
        """获取底部导航 Tab 列表

        请求体 (JSON):
        {
            "header": { "clientId": "xxx", "X-Token": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {}
        }

        响应:
        {
            "success": true,
            "data": [
                {
                    "id": 0,
                    "code": "home",
                    "name": "首页",
                    "nav_icon": null,
                    "nav_icon_active": null,
                    "is_home": true,
                    "sequence": 0
                },
                {
                    "id": 5,
                    "code": "deyu",
                    "name": "德育",
                    "nav_icon": "base64...",
                    "nav_icon_active": "base64...",
                    "is_home": false,
                    "sequence": 10
                }
            ]
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)  # noqa

            tabs = [{
                "id": 0,
                "code": "home",
                "name": "首页",
                "nav_icon": None,
                "nav_icon_active": None,
                "sequence": 0,
                "is_home": True,
            }]

            categories = request.env["learn.category"].sudo().search([
                ("parent_id", "=", False),
                ("show_in_nav", "=", True),
            ], order="sequence, id")

            for cat in categories:
                tabs.append({
                    "id": cat.id,
                    "code": cat.code,
                    "name": cat.name,
                    "nav_icon": encode_image(cat.nav_icon),
                    "nav_icon_active": encode_image(cat.nav_icon_active),
                    "sequence": cat.sequence,
                    "is_home": False,
                })

            return json_response(data=tabs)

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))


# ==================== 辅助函数 ====================

def _serialize_content(content, detail=False):
    """序列化内容对象"""
    data = {
        "id": content.id,
        "name": content.name,
        "content_type": content.content_type,
        "category_id": content.category_id.id,
        "category_name": content.category_id.name,
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


def _get_children(category, include_count=False):
    """递归获取子分类"""
    children = []
    for child in category.child_ids:
        item = {
            "id": child.id,
            "name": child.name,
            "code": child.code,
            "level": child.level,
            "is_leaf": child.is_leaf,
        }
        if include_count:
            item["content_count"] = child.content_count
        if child.child_ids:
            item["children"] = _get_children(child, include_count)
        children.append(item)
    return children


def _build_tree(category):
    """构建完整分类树"""
    node = {
        "id": category.id,
        "name": category.name,
        "code": category.code,
        "level": category.level,
        "is_leaf": category.is_leaf,
        "audience_type": category.audience_type,
        "stage_info": category.stage_info,
        "description": category.description,
        "content_count": category.content_count,
    }
    if category.child_ids:
        node["children"] = [_build_tree(c) for c in category.child_ids]
    return node


def _sync_wrong_book(session):
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
