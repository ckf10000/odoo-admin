# -*- coding: utf-8 -*-
"""试卷答题、批阅、成绩、错题本"""
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LearnExamSession(models.Model):
    """答题会话 - 用户每次作答产生一个会话"""

    _name = "learn.exam.session"
    _description = "答题会话"
    _order = "create_date desc"
    _inherit = ["mail.thread"]

    name = fields.Char(string="会话名称", compute="_compute_name", store=True)
    user_id = fields.Many2one(
        "res.users", string="用户",
        required=True, default=lambda self: self.env.uid,
        index=True,
    )
    content_id = fields.Many2one(
        "learn.content", string="试卷/练习册",
        required=True, ondelete="restrict",
        domain="[('content_type', 'in', ['exam', 'workbook'])]",
    )

    # ---- 会话状态 ----
    session_type = fields.Selection(
        selection=[
            ("practice", "练习模式"),
            ("exam", "考试模式"),
            ("retry", "错题重练"),
        ],
        string="模式",
        default="practice",
        required=True,
    )
    state = fields.Selection(
        selection=[
            ("in_progress", "进行中"),
            ("submitted", "已提交"),
            ("reviewed", "已批阅"),
        ],
        string="状态",
        default="in_progress",
        tracking=True,
    )

    # ---- 时间 ----
    start_time = fields.Datetime(string="开始时间", default=fields.Datetime.now)
    submit_time = fields.Datetime(string="提交时间")
    duration = fields.Float(
        string="耗时（分钟）", compute="_compute_duration", store=True,
    )

    # ---- 得分 ----
    total_score = fields.Float(string="总分", related="content_id.total_score", store=True)
    earned_score = fields.Float(string="得分", default=0.0)
    score_percent = fields.Float(
        string="得分率(%)", compute="_compute_score_percent", store=True,
    )
    is_passed = fields.Boolean(string="是否及格", compute="_compute_is_passed", store=True)

    # ---- 答题明细 ----
    answer_ids = fields.One2many(
        "learn.exam.answer", "session_id", string="答题明细",
    )
    correct_count = fields.Integer(
        string="正确题数", compute="_compute_correct_count", store=True,
    )
    wrong_count = fields.Integer(
        string="错误题数", compute="_compute_correct_count", store=True,
    )
    total_questions = fields.Integer(string="总题数", compute="_compute_correct_count", store=True)

    # ---- 错题来源标记 ----
    source_session_id = fields.Many2one(
        "learn.exam.session", string="来源会话",
        help="错题重练模式下，记录原始会话",
    )

    @api.depends("content_id.name", "create_date")
    def _compute_name(self):
        for record in self:
            if record.content_id:
                date_str = record.create_date.strftime("%m-%d %H:%M") if record.create_date else ""
                record.name = f"{record.content_id.name} - {date_str}"
            else:
                record.name = "答题会话"

    @api.depends("start_time", "submit_time")
    def _compute_duration(self):
        for record in self:
            if record.start_time and record.submit_time:
                delta = record.submit_time - record.start_time
                record.duration = round(delta.total_seconds() / 60.0, 1)
            else:
                record.duration = 0.0

    @api.depends("earned_score", "total_score")
    def _compute_score_percent(self):
        for record in self:
            if record.total_score > 0:
                record.score_percent = round(record.earned_score / record.total_score * 100, 1)
            else:
                record.score_percent = 0.0

    @api.depends("score_percent", "content_id.pass_score", "content_id.total_score")
    def _compute_is_passed(self):
        for record in self:
            pass_score = record.content_id.pass_score
            total = record.content_id.total_score
            if total > 0:
                record.is_passed = record.earned_score >= pass_score
            else:
                record.is_passed = False

    @api.depends("answer_ids", "answer_ids.is_correct")
    def _compute_correct_count(self):
        for record in self:
            answers = record.answer_ids
            record.total_questions = len(answers)
            record.correct_count = len(answers.filtered("is_correct"))
            record.wrong_count = record.total_questions - record.correct_count

    # ---- 业务方法 ----

    def action_start(self):
        """开始答题：根据模式生成答题明细"""
        self.ensure_one()
        if self.state != "in_progress":
            return

        existing = self.answer_ids
        if existing:
            return  # 已有明细，不重复生成

        # 获取题目
        if self.session_type == "retry" and self.source_session_id:
            # 错题重练：只取上次答错的题
            wrong_answers = self.source_session_id.answer_ids.filtered(
                lambda a: not a.is_correct
            )
            question_ids = wrong_answers.mapped("question_id")
        else:
            question_ids = self.content_id.question_ids

        if not question_ids:
            raise ValidationError("该试卷/练习册没有题目！")

        # 创建答题明细
        answers = []
        for q in question_ids:
            answers.append((0, 0, {
                "question_id": q.id,
                "score": q.score,
            }))
        self.write({"answer_ids": answers, "start_time": fields.Datetime.now()})

    def action_submit(self):
        """提交答卷"""
        self.ensure_one()
        self.state = "submitted"
        self.submit_time = fields.Datetime.now()

    def action_review(self):
        """自动批阅"""
        self.ensure_one()
        self.answer_ids._auto_review()  # noqa
        self.earned_score = sum(a.earned_score for a in self.answer_ids)
        self.state = "reviewed"

    def action_retry_wrong(self):
        """错题重练：创建新地答题会话，只包含错题"""
        self.ensure_one()
        wrong_answers = self.answer_ids.filtered(lambda a: not a.is_correct)
        if not wrong_answers:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "提示",
                    "message": "没有错题，无需重练！",
                    "type": "success",
                },
            }

        new_session = self.env["learn.exam.session"].create({
            "content_id": self.content_id.id,
            "session_type": "retry",
            "source_session_id": self.id,  # noqa
        })
        new_session.action_start()
        return {
            "type": "ir.actions.act_window",
            "name": "错题重练",
            "res_model": "learn.exam.session",
            "res_id": new_session.id,
            "view_mode": "form",
        }


class LearnExamAnswer(models.Model):
    """单题作答明细"""

    _name = "learn.exam.answer"
    _description = "答题明细"
    _order = "question_sequence"

    session_id = fields.Many2one(
        "learn.exam.session", string="答题会话",
        required=True, ondelete="cascade",
    )
    question_id = fields.Many2one(
        "learn.question", string="题目",
        required=True, ondelete="restrict",
    )
    question_sequence = fields.Integer(string="题号", related="question_id.sequence", store=True)

    # ---- 用户作答 ----
    user_answer = fields.Char(string="用户答案")
    # 对于选择题，存储选项字母如 "A" / "AB"
    # 对于填空/计算/问答，存储用户输入的文本

    # ---- 批阅结果 ----
    is_correct = fields.Boolean(string="是否正确")
    earned_score = fields.Float(string="得分", default=0.0)
    score = fields.Float(string="题目分值", default=5.0)

    # ---- 批阅备注 ----
    review_comment = fields.Text(string="批阅评语")

    # ---- 用户标记 ----
    is_marked_wrong = fields.Boolean(
        string="加入错题本", default=False,
        help="用户可手动标记此题加入错题本",
    )

    def _auto_review(self):
        """自动批阅：根据题目类型和正确答案比对"""
        for record in self:
            question = record.question_id
            user_ans = (record.user_answer or "").strip().upper()
            correct_ans = (question.correct_answer or "").strip().upper()

            if question.question_type in ("single_choice", "multi_choice", "true_false"):
                # 选择题/判断题：精确匹配
                record.is_correct = (user_ans == correct_ans)
                record.earned_score = record.score if record.is_correct else 0.0

            elif question.question_type == "fill_blank":
                # 填空题：支持多个空，用 | 分隔
                correct_parts = [p.strip().upper() for p in correct_ans.split("|") if p.strip()]
                user_parts = [p.strip().upper() for p in user_ans.split("|") if p.strip()]

                if len(correct_parts) == 0:
                    record.is_correct = (user_ans == correct_ans)
                else:
                    # 每个空独立判断
                    match_count = 0
                    for i, cp in enumerate(correct_parts):
                        if i < len(user_parts) and cp == user_parts[i]:
                            match_count += 1
                    per_blank_score = record.score / len(correct_parts) if correct_parts else record.score
                    record.earned_score = round(per_blank_score * match_count, 1)
                    record.is_correct = match_count == len(correct_parts)

            elif question.question_type == "calculation":
                # 计算题：数值比较（支持误差范围）
                try:
                    user_val = float(user_ans)
                    correct_val = float(correct_ans)
                    record.is_correct = abs(user_val - correct_val) < 0.001
                    record.earned_score = record.score if record.is_correct else 0.0
                except (ValueError, TypeError):
                    record.is_correct = (user_ans == correct_ans)
                    record.earned_score = record.score if record.is_correct else 0.0

            elif question.question_type == "essay":
                # 问答题：需人工批阅，默认 0 分
                record.is_correct = False
                record.earned_score = 0.0
                record.review_comment = "问答题需人工批阅"

            # 错题自动加入错题本
            if not record.is_correct:
                record.is_marked_wrong = True


class LearnWrongBook(models.Model):
    """错题本 - 汇总用户所有错题"""

    _name = "learn.wrong.book"
    _description = "错题本"
    _order = "create_date desc"

    user_id = fields.Many2one(
        "res.users", string="用户",
        required=True, default=lambda self: self.env.uid,
        index=True,
    )
    question_id = fields.Many2one(
        "learn.question", string="题目",
        required=True, ondelete="restrict",
    )
    content_id = fields.Many2one(
        "learn.content", string="所属试卷",
        related="question_id.content_id", store=True,
    )
    wrong_count = fields.Integer(string="错误次数", default=1)
    last_wrong_time = fields.Datetime(string="最近错误时间", default=fields.Datetime.now)
    is_mastered = fields.Boolean(string="已掌握", default=False)

    _sql_constraints = [
        ("unique_user_question",
         "UNIQUE(user_id, question_id)",
         "同一用户的同一题目只记录一次！"),
    ]

    def action_mastered(self):
        self.is_mastered = True

    def action_retry(self):
        """重新练习此题"""
        self.ensure_one()
        # 创建一个只包含此题的练习会话
        content = self.question_id.content_id
        session = self.env["learn.exam.session"].create({
            "content_id": content.id,
            "session_type": "retry",
        })
        # 只添加此题
        self.env["learn.exam.answer"].create({
            "session_id": session.id,
            "question_id": self.question_id.id,
            "score": self.question_id.score,
        })
        return {
            "type": "ir.actions.act_window",
            "name": "错题练习",
            "res_model": "learn.exam.session",
            "res_id": session.id,
            "view_mode": "form",
        }
