# -*- coding: utf-8 -*-
"""App 版本基线库 — 管理各平台的系统版本基线"""

from odoo import models, fields, api


class AppVersionBaseline(models.Model):
    _name = "app.version.baseline"
    _description = "版本基线库"
    _order = "platform, sequence, id"
    _sql_constraints = [
        ("unique_platform_version", "UNIQUE(platform, platform_version)",
         "同一平台的同一系统版本只能有一条基线记录！"),
    ]

    name = fields.Char(string="基线名称", required=True, compute="_compute_name", store=True)
    sequence = fields.Integer(string="排序", default=10)

    # ---- 平台信息 ----
    platform = fields.Selection(
        selection=[
            ("ios", "iOS"),
            ("android", "Android"),
            ("harmonyos", "HarmonyOS"),
        ],
        string="平台",
        required=True,
    )
    platform_version = fields.Char(
        string="平台版本",
        required=True,
        help="如：iOS 18.0, Android 14, HarmonyOS 4.0",
    )
    platform_version_code = fields.Char(
        string="版本代号",
        help="内部代号，如 SDK 版本号",
    )

    # ---- 状态 ----
    active = fields.Boolean(string="启用", default=True)
    is_deprecated = fields.Boolean(
        string="已弃用",
        help="标记该平台版本已不再支持",
    )
    deprecation_date = fields.Date(string="弃用日期")

    # ---- 描述 ----
    description = fields.Text(string="备注说明")

    # ---- 关联统计 ----
    release_count = fields.Integer(
        string="发布数量", compute="_compute_release_count", store=True,
    )
    terminal_count = fields.Integer(
        string="终端数量", compute="_compute_terminal_count", store=True,
    )

    @api.depends("platform", "platform_version")
    def _compute_name(self):
        for record in self:
            platform_label = dict(self._fields["platform"].selection).get(record.platform, "")  # noqa
            record.name = f"{platform_label} {record.platform_version}"

    @api.depends("platform")
    def _compute_release_count(self):
        for record in self:
            record.release_count = self.env["app.release"].search_count([
                ("baseline_id", "=", record.id),
            ])

    @api.depends("platform")
    def _compute_terminal_count(self):
        for record in self:
            record.terminal_count = self.env["app.terminal"].search_count([
                ("platform", "=", record.platform),
                ("active", "=", True),
            ])

    def action_view_releases(self):
        """跳转到关联发布列表"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"{self.name} - 发布记录",
            "res_model": "app.release",
            "view_mode": "tree,form",
            "domain": [("baseline_id", "=", self.id)],  # noqa
        }
