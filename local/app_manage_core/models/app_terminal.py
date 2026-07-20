# -*- coding: utf-8 -*-
"""App 终端管理 — 设备型号白名单"""

from odoo import models, fields, api


class AppTerminal(models.Model):
    _name = "app.terminal"
    _description = "终端管理"
    _order = "platform, terminal_type, sequence, id"
    _sql_constraints = [
        ("unique_terminal_model", "UNIQUE(platform, terminal_model)",
         "同一平台下终端型号必须唯一！"),
    ]

    name = fields.Char(string="终端名称", compute="_compute_name", store=True)
    sequence = fields.Integer(string="排序", default=10)
    active = fields.Boolean(string="启用", default=True)

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
    terminal_type = fields.Selection(
        selection=[
            ("phone", "手机"),
            ("tablet", "平板"),
            ("foldable", "折叠屏"),
            ("tv", "电视"),
            ("watch", "手表"),
            ("car", "车机"),
        ],
        string="终端类型",
        required=True,
    )

    # ---- 型号信息 ----
    terminal_model = fields.Char(
        string="终端型号",
        required=True,
        help="如：iPhone 15 Pro Max, iPad Pro 12.9, Mate 60 Pro",
    )
    terminal_code = fields.Char(
        string="终端代码",
        help="设备标识符，如：iPhone16,2, SM-S9280",
    )
    manufacturer = fields.Char(string="制造商")

    # ---- 版本限制 ----
    min_os_version = fields.Char(
        string="最低系统版本",
        help="低于此系统版本的设备将不被支持",
    )
    max_os_version = fields.Char(string="最高系统版本")

    # ---- 白名单标识 ----
    is_whitelisted = fields.Boolean(
        string="白名单设备",
        default=True,
        help="取消勾选后，此设备型号将被拒绝安装",
    )

    # ---- 发布关联 ----
    baseline_ids = fields.Many2many(
        "app.version.baseline", "app_terminal_baseline_rel",
        "terminal_id", "baseline_id",
        string="关联基线版本",
    )

    # ---- 备注 ----
    description = fields.Text(string="备注说明")

    @api.depends("platform", "terminal_type", "terminal_model")
    def _compute_name(self):
        for record in self:
            platform_label = dict(self._fields["platform"].selection).get(record.platform, "")  # noqa
            type_label = dict(self._fields["terminal_type"].selection).get(record.terminal_type, "")  # noqa
            record.name = f"{platform_label} {type_label} - {record.terminal_model}"

    @api.model
    def check_terminal_allowed(self, platform, terminal_model):
        """校验终端是否在白名单内
        :return: (is_allowed: bool, message: str)
        """
        terminal = self.sudo().search([
            ("platform", "=", platform),
            ("terminal_model", "=", terminal_model),
            ("active", "=", True),
        ], limit=1)

        if not terminal:
            return False, f"设备型号 {terminal_model} 未在支持列表中"
        if not terminal.is_whitelisted:
            return False, f"设备型号 {terminal_model} 已被列入黑名单"
        return True, "OK"
