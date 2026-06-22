# -*- coding: utf-8 -*-
"""App 渠道管理 — 渠道商、渠道白名单"""

from odoo import models, fields


class AppChannel(models.Model):
    _name = "app.channel"
    _description = "渠道管理"
    _order = "sequence, id"
    _sql_constraints = [
        ("unique_channel_code", "UNIQUE(channel_code)", "渠道编码必须唯一！"),
    ]

    name = fields.Char(string="渠道名称", required=True)
    channel_code = fields.Char(string="渠道编码", required=True, help="唯一标识，如：huawei, xiaomi, appstore")
    sequence = fields.Integer(string="排序", default=10)
    active = fields.Boolean(string="启用", default=True)

    # ---- 渠道信息 ----
    channel_type = fields.Selection(
        selection=[
            ("official", "官方渠道"),
            ("third_party", "第三方应用市场"),
            ("enterprise", "企业内部分发"),
            ("test", "测试渠道"),
        ],
        string="渠道类型",
        default="official",
    )
    platform = fields.Selection(
        selection=[
            ("ios", "iOS"),
            ("android", "Android"),
            ("harmonyos", "HarmonyOS"),
            ("all", "全平台"),
        ],
        string="适用平台",
    )

    # ---- 白名单配置 ----
    use_whitelist = fields.Boolean(string="启用白名单", help="开启后仅白名单用户可使用此渠道")
    whitelist_mode = fields.Selection(
        selection=[
            ("user", "按用户"),
            ("organization", "按组织/企业"),
            ("region", "按地区"),
        ],
        string="白名单模式",
        default="user",
    )
    whitelist_user_ids = fields.Many2many(
        "res.users", "app_channel_user_rel",
        "channel_id", "user_id",
        string="白名单用户",
        help="此渠道仅允许这些用户访问",
    )
    whitelist_partner_ids = fields.Many2many(
        "res.partner", "app_channel_partner_rel",
        "channel_id", "partner_id",
        string="白名单组织",
        help="此渠道仅允许这些组织的用户访问",
    )

    # ---- 渠道配置 ----
    download_url_template = fields.Char(string="下载地址模板")
    app_store_id = fields.Char(string="应用市场 ID", help="如 App Store ID、华为应用市场包名")

    # ---- 备注 ----
    description = fields.Text(string="备注说明")
