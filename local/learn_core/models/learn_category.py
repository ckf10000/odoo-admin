# -*- coding: utf-8 -*-
from odoo import models, fields, api

"""学习分类模型 - 自引用树形结构，支持无限层级"""


class LearnCategory(models.Model):
    _name = "learn.category"
    _description = "学习分类"
    _order = "sequence, id"
    _parent_store = True

    name = fields.Char(string="分类名称", required=True, translate=True)
    code = fields.Char(string="分类编码", help="唯一编码，用于 API 查询")
    sequence = fields.Integer(string="排序", default=10)

    # ---- 树形结构 ----
    parent_id = fields.Many2one(
        "learn.category", string="上级分类",
        ondelete="restrict", index=True,
    )
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many("learn.category", "parent_id", string="子分类")

    # ---- 层级信息 ----
    level = fields.Integer(string="层级", compute="_compute_level", store=True, recursive=True)
    is_leaf = fields.Boolean(string="是否末级分类", compute="_compute_is_leaf", store=True)

    # ---- 业务标识 ----
    audience_type = fields.Selection(
        selection=[
            ("enlightenment", "思维启蒙"),
            ("children", "少儿教育"),
            ("nine_year", "九年义务"),
            ("adult", "成人教育"),
        ],
        string="受众人群",
        help="第一层分类的受众标识",
    )

    stage_info = fields.Char(string="阶段/年级", help="如：一年级、1-3岁、计算机")

    # ---- 描述 ----
    description = fields.Text(string="描述")

    # ---- 关联内容数量（统计用） ----
    content_count = fields.Integer(
        string="内容数量", compute="_compute_content_count", store=True,
    )
    word_count = fields.Integer(
        string="单词数量", compute="_compute_word_count", store=True,
    )
    item_count = fields.Integer(
        string="知识点数量", compute="_compute_item_count", store=True,
    )

    _sql_constraints = [
        ("unique_code", "UNIQUE(code)", "分类编码必须唯一！"),
    ]

    @api.depends("parent_id", "parent_id.level")
    def _compute_level(self):
        for record in self:
            if not record.parent_id:
                record.level = 0
            else:
                record.level = record.parent_id.level + 1

    @api.depends("child_ids")
    def _compute_is_leaf(self):
        for record in self:
            record.is_leaf = not bool(record.child_ids)

    @api.depends("child_ids")
    def _compute_content_count(self):
        """统计当前分类及所有子分类下的内容总数"""
        for record in self:
            all_categories = record._get_all_child_ids()  # noqa
            record.content_count = self.env["learn.content"].search_count([
                ("category_id", "in", all_categories),
            ])

    @api.depends("child_ids")
    def _compute_word_count(self):
        """统计当前分类及所有子分类下的单词总数（旧 learn.word 模型）"""
        for record in self:
            all_categories = record._get_all_child_ids()  # noqa
            contents = self.env["learn.content"].search([
                ("category_id", "in", all_categories),
            ])
            record.word_count = self.env["learn.word"].search_count([
                ("content_id", "in", contents.ids),
            ])

    @api.depends("child_ids")
    def _compute_item_count(self):
        """统计当前分类及所有子分类下的知识点条目总数（新 learn.item 模型）"""
        for record in self:
            all_categories = record._get_all_child_ids()  # noqa
            contents = self.env["learn.content"].search([
                ("category_id", "in", all_categories),
            ])
            record.item_count = self.env["learn.item"].search_count([
                ("content_id", "in", contents.ids),
            ])

    def _get_all_child_ids(self):
        """递归获取所有子分类 ID（含自身）"""
        self.ensure_one()
        result = [self.id]  # noqa
        for child in self.child_ids:
            result.extend(child._get_all_child_ids())  # noqa
        return result

    def action_view_contents(self):
        """跳转到关联内容列表"""
        self.ensure_one()
        all_cats = self._get_all_child_ids()
        return {
            "type": "ir.actions.act_window",
            "name": f"{self.name} - 学习内容",
            "res_model": "learn.content",
            "view_mode": "tree,form",
            "domain": [("category_id", "in", all_cats)],
            "context": {"default_category_id": self.id},  # noqa
        }

    def action_view_words(self):
        """跳转到关联单词列表（旧 learn.word）"""
        self.ensure_one()
        all_cats = self._get_all_child_ids()
        contents = self.env["learn.content"].search([
            ("category_id", "in", all_cats),
        ])
        return {
            "type": "ir.actions.act_window",
            "name": f"{self.name} - 单词列表",
            "res_model": "learn.word",
            "view_mode": "tree,form",
            "domain": [("content_id", "in", contents.ids)],
        }

    def action_view_items(self):
        """跳转到关联知识点列表（新 learn.item，支持按类型筛选）"""
        self.ensure_one()
        all_cats = self._get_all_child_ids()
        contents = self.env["learn.content"].search([
            ("category_id", "in", all_cats),
        ])
        return {
            "type": "ir.actions.act_window",
            "name": f"{self.name} - 知识点",
            "res_model": "learn.item",
            "view_mode": "tree,form",
            "domain": [("content_id", "in", contents.ids)],
        }
