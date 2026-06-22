# -*- coding: utf-8 -*-
"""App 素材管理 — 离线 icon、在线 icon、启动图等"""

from odoo import models, fields


class AppResource(models.Model):
    _name = "app.resource"
    _description = "素材管理"
    _order = "resource_type, sequence, id"

    name = fields.Char(string="素材名称", required=True)
    sequence = fields.Integer(string="排序", default=10)
    active = fields.Boolean(string="启用", default=True)

    # ---- 素材类型 ----
    resource_type = fields.Selection(
        selection=[
            ("app_icon", "App 图标"),
            ("launch_screen", "启动图"),
            ("splash_ad", "开屏广告"),
            ("tab_icon", "Tab 图标"),
            ("placeholder", "占位图"),
            ("empty_state", "空状态图"),
            ("loading", "加载动画"),
            ("other", "其他"),
        ],
        string="素材类型",
        required=True,
    )

    # ---- 平台/版本关联 ----
    platform = fields.Selection(
        selection=[
            ("ios", "iOS"),
            ("android", "Android"),
            ("harmonyos", "HarmonyOS"),
            ("all", "全平台"),
        ],
        string="适用平台",
        default="all",
    )
    baseline_id = fields.Many2one(
        "app.version.baseline", string="适用基线版本",
        help="留空则适用所有版本",
    )
    min_app_version_code = fields.Integer(
        string="最低 App 版本代码",
        help="低于此版本的 App 不加载此素材",
    )

    # ---- 素材资源 ----
    offline_file = fields.Binary(
        string="离线素材文件", attachment=True,
        help="打包进 App 的离线素材",
    )
    offline_filename = fields.Char(string="离线文件名")
    online_url = fields.Char(
        string="在线素材 URL",
        help="在线动态更新素材的 URL",
    )
    file_size = fields.Integer(string="文件大小(字节)", compute="_compute_file_size", store=True)

    # ---- 尺寸规范 ----
    resolution = fields.Char(string="分辨率", help="如：1024x1024, 1920x1080")
    density = fields.Char(string="像素密度", help="如：mdpi, hdpi, xhdpi, xxhdpi, @2x, @3x")

    # ---- 更新策略 ----
    is_force_update = fields.Boolean(
        string="强制更新",
        help="勾选后，App 启动时必须检查并下载最新素材",
    )
    update_interval_hours = fields.Integer(
        string="更新检查间隔(小时)",
        default=24,
        help="App 检查素材更新的时间间隔",
    )

    # ---- 描述 ----
    description = fields.Text(string="描述说明")

    _sql_constraints = [
        ("unique_offline_filename", "UNIQUE(offline_filename)",
         "离线文件名必须唯一！"),
    ]

    def _compute_file_size(self):
        for record in self:
            record.file_size = len(record.offline_file) if record.offline_file else 0
