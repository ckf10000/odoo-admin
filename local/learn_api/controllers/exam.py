# -*- coding: utf-8 -*-
"""考试 / 错题本 API"""
from odoo import http
from odoo.http import request

from .common import json_response, error_response, api_verify_auth, sync_wrong_book  # noqa


class LearnExamController(http.Controller):

    @http.route("/api/v1/learn/exam/start", type="http", auth="public", methods=["POST"], csrf=False)
    def start_exam(self, **kw):  # noqa
        """开始答题"""
        try:
            header, body, user = api_verify_auth(require_token=True)
            vals = {"content_id": body.get("content_id"), "session_type": body.get("session_type", "practice"),
                    "user_id": user.id}
            sid = body.get("source_session_id")
            if sid:
                vals["source_session_id"] = sid
            session = request.env["learn.exam.session"].sudo().create(vals)
            session.action_start()
            answers = []
            for a in session.answer_ids:
                q = a.question_id
                answers.append({
                    "id": a.id, "question_id": q.id, "question_type": q.question_type,
                    "stem": q.stem,
                    "options": {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d, "E": q.option_e,
                                "F": q.option_f}
                    if q.question_type in ("single_choice", "multi_choice") else None,
                    "score": q.score, "user_answer": None, "is_correct": None,
                })
            return json_response(data={
                "session_id": session.id, "content_name": session.content_id.name,
                "total_score": session.content_id.total_score, "pass_score": session.content_id.pass_score,
                "time_limit": session.content_id.time_limit, "answers": answers,
            })
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/exam/save_answer", type="http", auth="public", methods=["POST"], csrf=False)
    def save_answer(self, **kw):  # noqa
        """保存单题答案"""
        try:
            header, body, user = api_verify_auth(require_token=True)
            answer = request.env["learn.exam.answer"].sudo().browse(body.get("answer_id"))
            if not answer.exists():
                return error_response("答题明细不存在", 404)
            if answer.session_id.user_id.id != user.id:
                return error_response("无权操作", 403)
            answer.write({"user_answer": body.get("user_answer", "")})
            return json_response(data={"id": answer.id, "saved": True})
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/exam/submit", type="http", auth="public", methods=["POST"], csrf=False)
    def submit_exam(self, **kw):  # noqa
        """提交试卷并自动批阅"""
        try:
            header, body, user = api_verify_auth(require_token=True)
            session = request.env["learn.exam.session"].sudo().browse(body.get("session_id"))
            if not session.exists():
                return error_response("会话不存在", 404)
            if session.user_id.id != user.id:
                return error_response("无权操作", 403)
            if session.state != "in_progress":
                return error_response("该会话已提交", 400)
            session.action_submit()
            session.action_review()
            sync_wrong_book(session)
            return json_response(data={
                "session_id": session.id, "total_score": session.total_score, "earned_score": session.earned_score,
                "score_percent": session.score_percent, "is_passed": session.is_passed,
                "correct_count": session.correct_count, "wrong_count": session.wrong_count,
                "total_questions": session.total_questions, "duration": session.duration,
                "answers": [{
                    "id": a.id, "question_id": a.question_id.id, "question_type": a.question_id.question_type,
                    "stem": a.question_id.stem, "user_answer": a.user_answer,
                    "correct_answer": a.question_id.correct_answer,
                    "explanation": a.question_id.answer_explanation, "is_correct": a.is_correct,
                    "earned_score": a.earned_score, "score": a.score,
                } for a in session.answer_ids],
            })
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))

    @http.route("/api/v1/learn/exam/history", type="http", auth="public", methods=["POST"], csrf=False)
    def exam_history(self, **kw):  # noqa
        """成绩历史"""
        try:
            header, body, user = api_verify_auth(require_token=True)
            domain = [("user_id", "=", user.id), ("state", "=", "reviewed")]
            cid = body.get("content_id")
            if cid:
                domain.append(("content_id", "=", int(cid)))
            page = max(1, int(body.get("page", 1)))
            page_size = min(100, max(1, int(body.get("page_size", 20))))
            total = request.env["learn.exam.session"].sudo().search_count(domain)
            sessions = request.env["learn.exam.session"].sudo().search(
                domain, offset=(page - 1) * page_size, limit=page_size, order="create_date desc")
            return json_response(data={
                "list": [{
                    "id": s.id, "name": s.name, "content_id": s.content_id.id, "content_name": s.content_id.name,
                    "session_type": s.session_type, "total_score": s.total_score, "earned_score": s.earned_score,
                    "score_percent": s.score_percent, "is_passed": s.is_passed,
                    "correct_count": s.correct_count, "wrong_count": s.wrong_count,
                    "total_questions": s.total_questions, "duration": s.duration,
                    "create_date": str(s.create_date),
                } for s in sessions],
                "total": total, "page": page, "page_size": page_size,
            })
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))


class LearnWrongBookController(http.Controller):

    @http.route("/api/v1/learn/wrong_book", type="http", auth="public", methods=["POST"], csrf=False)
    def get_wrong_book(self, **kw):  # noqa
        """获取错题本（分页）"""
        try:
            header, body, user = api_verify_auth(require_token=True)
            domain = [("user_id", "=", user.id), ("is_mastered", "=", False)]
            cid = body.get("content_id")
            if cid:
                domain.append(("content_id", "=", int(cid)))
            page = max(1, int(body.get("page", 1)))
            page_size = min(100, max(1, int(body.get("page_size", 20))))
            total = request.env["learn.wrong.book"].sudo().search_count(domain)
            records = request.env["learn.wrong.book"].sudo().search(
                domain, offset=(page - 1) * page_size, limit=page_size, order="last_wrong_time desc")
            return json_response(data={
                "list": [{
                    "id": wb.id, "question_id": wb.question_id.id, "question_type": wb.question_id.question_type,
                    "stem": wb.question_id.stem, "correct_answer": wb.question_id.correct_answer,
                    "explanation": wb.question_id.answer_explanation, "difficulty": wb.question_id.difficulty,
                    "content_id": wb.content_id.id, "content_name": wb.content_id.name,
                    "wrong_count": wb.wrong_count, "last_wrong_time": str(wb.last_wrong_time),
                } for wb in records],
                "total": total, "page": page, "page_size": page_size,
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
