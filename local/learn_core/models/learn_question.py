# -*- coding: utf-8 -*-
from odoo import models, fields


class LearnQuestion(models.Model):
    _name = "learn.question"
    _description = "题目"
    _order = "id"

    name = fields.Char(string="题目标题")

    # 关联选择器，用于按年级/科目/版本等维度筛选题目
    selector_ids = fields.Many2many(
        "learn.selector", "learn_question_selector_rel", "question_id", "selector_id", string="适用选择器",
    )

    # ---- 题目类型 ----
    question_type = fields.Selection(
        selection='_get_question_type_selection',
        string="内容类型",
        required=True,
        default="single_choice",
    )

    def _get_question_type_selection(self):
        """动态从 learn.content.type 中读取 storage_model='learn.question' 的所有 code"""
        types = self.env['learn.content.type'].sudo().search([
            ('storage_model', '=', 'learn.question'),
        ])
        return [(t.code, t.name) for t in types]

    # ---- 题目内容 ----
    stem = fields.Html(string="题干", required=True)
    stem_image = fields.Binary(string="题干图片", attachment=True)

    # ---- 选项（选择题用） ----
    option_a = fields.Char(string="选项 A")
    option_b = fields.Char(string="选项 B")
    option_c = fields.Char(string="选项 C")
    option_d = fields.Char(string="选项 D")
    option_e = fields.Char(string="选项 E")
    option_f = fields.Char(string="选项 F")

    # ---- 答案 ----
    # 选择题：存储正确答案选项，如 "A" / "AB" / "ACD"
    correct_answer = fields.Char(string="正确答案")
    # 填空题/计算题/问答题的参考答案
    reference_answer = fields.Text(string="参考答案")
    # 答案解析
    answer_explanation = fields.Html(string="答案解析")

    # ---- 分值 ----
    default_score = fields.Float(string="默认分值", default=5.0, help="编排时自动带入，可覆盖")

    # ---- 难度 ----
    difficulty = fields.Selection(
        selection=[
            ("easy", "简单"),
            ("medium", "中等"),
            ("hard", "困难"),
        ],
        string="难度",
        default="medium",
    )

    _sql_constraints = [
        # 序号和分值已移到 learn.group.line 层控制，此处不再需要
    ]
