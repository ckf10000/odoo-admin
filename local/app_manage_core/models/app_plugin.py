# -*- coding: utf-8 -*-
"""App 插件管理 — 插件上传、分发策略"""

from odoo import models, fields, api
from odoo.exceptions import UserError


class AppPlugin(models.Model):
    _name = "app.plugin"
    _description = "插件管理"
    _order = "sequence, id"
    _sql_constraints = [
        ("unique_plugin_code", "UNIQUE(plugin_code)", "插件编码必须唯一！"),
    ]

    name = fields.Char(string="插件名称", required=True)
    plugin_code = fields.Char(string="插件编码", required=True, help="唯一标识，如：ocr, ar_core, push")
    sequence = fields.Integer(string="排序", default=10)
    active = fields.Boolean(string="启用", default=True)

    # ---- 插件基本信息 ----
    plugin_type = fields.Selection(
        selection=[
            ("core", "核心插件"),
            ("feature", "功能插件"),
            ("theme", "主题插件"),
            ("third_party", "第三方插件"),
        ],
        string="插件类型",
        default="feature",
    )
    platform = fields.Selection(
        selection=[
            ("ios", "iOS"),
            ("android", "Android"),
            ("harmonyos", "HarmonyOS"),
            ("all", "全平台"),
        ],
        string="适用平台",
        required=True,
    )

    # ---- 当前版本信息 ----
    current_version = fields.Char(
        string="当前版本号",
        compute="_compute_current_version", store=True, compute_sudo=True,
    )
    current_version_code = fields.Integer(
        string="当前版本代码",
        compute="_compute_current_version", store=True, compute_sudo=True,
    )
    current_package_file = fields.Binary(
        string="当前插件包",
        compute="_compute_current_package_file", store=False,
        help="取最新发布版本的插件包",
    )

    # ---- 分发策略 ----
    distribution_mode = fields.Selection(
        selection=[
            ("mandatory", "强制分发"),
            ("optional", "非强制分发"),
            ("silent", "静默更新"),
        ],
        string="默认分发模式",
        default="optional",
    )
    auto_update = fields.Boolean(string="自动更新", default=False)
    require_restart = fields.Boolean(
        string="需要重启",
        help="安装/更新后是否需要重启 App",
    )

    # ---- 依赖 ----
    min_app_version_code = fields.Integer(
        string="最低 App 版本代码",
        help="低于此版本的 App 不能加载此插件",
    )
    dependency_plugin_ids = fields.Many2many(
        "app.plugin", "app_plugin_dependency_rel",
        "plugin_id", "dependency_id",
        string="依赖插件",
        help="此插件依赖的其他插件",
    )

    # ---- 描述 ----
    description = fields.Text(string="插件描述")
    icon = fields.Binary(string="插件图标", attachment=True)

    # ---- 关联发布记录 ----
    release_ids = fields.One2many(
        "app.plugin.release", "plugin_id", string="发布记录",
    )
    release_count = fields.Integer(
        string="发布次数", compute="_compute_release_count", store=True,
    )

    @api.depends("release_ids.state", "release_ids.version_code")
    def _compute_current_version(self):
        for record in self:
            latest = record.release_ids.filtered(
                lambda r: r.state == "published"
            ).sorted("version_code", reverse=True)
            if latest:
                record.current_version = latest[0].version
                record.current_version_code = latest[0].version_code
            else:
                record.current_version = None
                record.current_version_code = 0

    @api.depends("release_ids.state", "release_ids.version_code", "release_ids.package_file")
    def _compute_current_package_file(self):
        for record in self:
            latest = record.release_ids.filtered(
                lambda r: r.state == "published"
            ).sorted("version_code", reverse=True)
            record.current_package_file = latest[0].package_file if latest else None

    @api.depends("release_ids")
    def _compute_release_count(self):
        for record in self:
            record.release_count = len(record.release_ids)

    def action_view_releases(self):
        """查看发布记录"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"{self.name} - 发布记录",
            "res_model": "app.plugin.release",
            "view_mode": "tree,form",
            "domain": [("plugin_id", "=", self.id)],  # noqa
        }

    @api.model
    def get_plugin_info_for_check(self, plugin_code, current_version_code=0):
        """获取插件校验信息（供 API 调用）
        :return: dict with needs_update, force_update, latest_version, latest_version_code, package_url, etc.
        """
        plugin = self.sudo().search([
            ("plugin_code", "=", plugin_code),
            ("active", "=", True),
        ], limit=1)
        if not plugin:
            return {"exists": False, "message": f"插件 {plugin_code} 不存在"}

        needs_update = plugin.current_version_code > current_version_code
        latest_release = plugin.release_ids.filtered(
            lambda r: r.state == "published"
        ).sorted("version_code", reverse=True)

        result = {
            "exists": True,
            "plugin_code": plugin.plugin_code,
            "plugin_name": plugin.name,
            "current_version": current_version_code,
            "latest_version": plugin.current_version,
            "latest_version_code": plugin.current_version_code,
            "needs_update": needs_update,
        }

        if latest_release:
            result.update({
                "distribution_mode": latest_release[0].distribution_mode,
                "force_update": latest_release[0].distribution_mode == "mandatory",
                "require_restart": latest_release[0].require_restart,
                "release_note": latest_release[0].release_note,
                "download_url": latest_release[0].download_url,
                "package_size": latest_release[0].package_size,
            })

        return result


class AppPluginRelease(models.Model):
    _name = "app.plugin.release"
    _description = "插件发布记录"
    _order = "version_code desc, id"

    name = fields.Char(string="发布名称", compute="_compute_name", store=True)

    # ---- 关联插件 ----
    plugin_id = fields.Many2one(
        "app.plugin", string="插件",
        required=True, ondelete="cascade", index=True,
    )

    # ---- 版本信息 ----
    version = fields.Char(string="版本号", required=True)
    version_code = fields.Integer(
        string="版本代码", required=True,
        help="必须与插件打包时的 versionCode 完全一致，整数递增，用于版本比较",
    )

    # ---- 分发策略（可覆盖插件默认策略） ----
    distribution_mode = fields.Selection(
        selection=[
            ("mandatory", "强制分发"),
            ("optional", "非强制分发"),
            ("silent", "静默更新"),
        ],
        string="分发模式",
        default="optional",
    )
    require_restart = fields.Boolean(string="需要重启")

    # ---- 发布内容 ----
    release_note = fields.Html(string="Release Note")
    change_log = fields.Text(string="变更日志")

    # ---- 附件 ----
    oss_config_id = fields.Many2one(
        "app.oss.config", string="OSS 配置",
        help="选择用于上传插件包的 OSS 配置，留空则使用默认启用的配置",
    )
    package_file = fields.Binary(string="插件包文件", attachment=True)
    package_filename = fields.Char(string="插件包文件名")
    package_size = fields.Integer(string="包大小(字节)", compute="_compute_package_size", store=True)
    download_url = fields.Char(string="下载地址", readonly=True)

    # ---- 状态 ----
    state = fields.Selection(
        selection=[
            ("draft", "草稿"),
            ("testing", "测试中"),
            ("published", "已发布"),
            ("revoked", "已撤回"),
        ],
        string="状态",
        default="draft",
    )
    publish_date = fields.Datetime(string="发布日期")

    # ---- 兼容性 ----
    min_app_version_code = fields.Integer(string="最低 App 版本代码")
    max_app_version_code = fields.Integer(string="最高 App 版本代码")

    # ---- 备注 ----
    description = fields.Text(string="备注说明")

    @api.depends("plugin_id.name", "version")
    def _compute_name(self):
        for record in self:
            plugin_name = record.plugin_id.name or ""
            record.name = f"{plugin_name} v{record.version}"

    @api.depends("package_file")
    def _compute_package_size(self):
        for record in self:
            record.package_size = len(record.package_file) if record.package_file else 0

    def action_upload_to_oss(self):
        """手动上传插件包到 OSS 并回填 download_url"""
        self.ensure_one()
        if not self.package_file:
            raise UserError("请先上传插件包文件")
        url = self.env["app.oss.config"].upload_file(
            self.package_file,
            self.package_filename or "plugin_package.zip",
        )
        if url:
            self.download_url = url
        else:
            raise UserError("OSS 上传失败，请检查 OSS 配置")

    def write(self, vals):
        """已发布状态不允许编辑；草稿状态保留附件不删除"""
        for record in self:
            if record.state == "published" and not self.env.context.get("allow_revoke_write"):
                raise UserError("已发布的插件版本不允许编辑，请先撤回后再修改")
        return super().write(vals)

    @api.constrains("state", "plugin_id", "version")
    def _check_unique_published_version(self):
        """同一插件下的已发布版本号必须唯一"""
        for record in self:
            if record.state != "published":
                continue
            duplicate = self.search([
                ("id", "!=", record.id),
                ("plugin_id", "=", record.plugin_id.id),
                ("version", "=", record.version),
                ("state", "=", "published"),
            ], limit=1)
            if duplicate:
                raise UserError(
                    f"同一插件 ({record.plugin_id.name}) 下已存在已发布的版本 {record.version}，"
                    f"请先撤回旧版本或使用新的版本号"
                )

    def action_publish(self):
        """发布（先校验通过后再上传到 OSS）"""
        for record in self:
            if not record.package_file:
                raise UserError("请先上传插件包文件")
        self.write({
            "state": "published",
            "publish_date": fields.Datetime.now(),

        })
        for record in self:
            if not record.download_url:
                record.action_upload_to_oss()

    def action_revoke(self):
        self.with_context(allow_revoke_write=True).write({"state": "revoked"})
