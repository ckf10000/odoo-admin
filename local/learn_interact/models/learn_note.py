# -*- coding: utf-8 -*-
"""收藏、批注、笔记、评论"""

from odoo import models, fields, api


class LearnFavorite(models.Model):
    """收藏"""

    _name = "learn.favorite"
    _description = "内容收藏"
    _order = "create_date desc"

    user_id = fields.Many2one(
        "res.users", string="用户",
        required=True, default=lambda self: self.env.uid,
        index=True,
    )
    content_id = fields.Many2one(
        "learn.content", string="内容",
        required=True, ondelete="cascade",
        index=True,
    )
    content_name = fields.Char(string="内容标题", related="content_id.name")
    content_type = fields.Selection(string="内容类型", related="content_id.content_type")

    _sql_constraints = [
        ("unique_user_content",
         "UNIQUE(user_id, content_id)",
         "您已经收藏过此内容！"),
    ]


class LearnAnnotation(models.Model):
    """批注 - 在教材/文档上做标注"""

    _name = "learn.annotation"
    _description = "内容批注"
    _order = "page_number, create_date"

    user_id = fields.Many2one(
        "res.users", string="用户",
        required=True, default=lambda self: self.env.uid,
        index=True,
    )
    content_id = fields.Many2one(
        "learn.content", string="内容",
        required=True, ondelete="cascade",
        index=True,
        domain="[('content_type', 'in', ['textbook'])]",
    )

    # ---- 定位 ----
    page_number = fields.Integer(string="页码", required=True)
    position_x = fields.Float(string="X 坐标(%)")
    position_y = fields.Float(string="Y 坐标(%)")
    selected_text = fields.Text(string="选中文本")

    # ---- 批注内容 ----
    annotation_type = fields.Selection(
        selection=[
            ("highlight", "高亮"),
            ("underline", "下划线"),
            ("note", "批注"),
            ("bookmark", "书签"),
        ],
        string="批注类型",
        default="highlight",
    )
    annotation_text = fields.Text(string="批注文字")
    color = fields.Char(string="颜色", default="#FFEB3B")


class LearnNote(models.Model):
    """笔记"""

    _name = "learn.note"
    _description = "学习笔记"
    _order = "create_date desc"

    user_id = fields.Many2one(
        "res.users", string="用户",
        required=True, default=lambda self: self.env.uid,
        index=True,
    )
    content_id = fields.Many2one(
        "learn.content", string="关联内容",
        required=True, ondelete="cascade",
        index=True,
    )

    title = fields.Char(string="笔记标题", required=True)
    content = fields.Html(string="笔记内容")
    page_number = fields.Integer(string="关联页码")

    # 可见性
    is_private = fields.Boolean(string="私有", default=True,
                                help="私有笔记仅自己可见")


class LearnRating(models.Model):
    """评分与评论"""

    _name = "learn.rating"
    _description = "内容评分与评论"
    _order = "create_date desc"
    _inherit = ["mail.thread"]

    user_id = fields.Many2one(
        "res.users", string="用户",
        required=True, default=lambda self: self.env.uid,
        index=True,
    )
    content_id = fields.Many2one(
        "learn.content", string="内容",
        required=True, ondelete="cascade",
        index=True,
    )

    score = fields.Integer(string="评分", required=True,
                           help="1-5 星评分")
    comment = fields.Text(string="评论")
    is_approved = fields.Boolean(string="已审核", default=True)

    _sql_constraints = [
        ("unique_user_content_rating",
         "UNIQUE(user_id, content_id)",
         "您已经评价过此内容！"),
    ]

    @api.constrains("score")
    def _check_score(self):
        for record in self:
            if record.score < 1 or record.score > 5:
                from odoo.exceptions import ValidationError
                raise ValidationError("评分必须在 1-5 之间！")
