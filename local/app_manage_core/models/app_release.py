# -*- coding: utf-8 -*-
"""App 发布管理 — 版本发布、Release Note、强制更新、依赖"""

from odoo import models, fields, api
from odoo.exceptions import UserError


class AppRelease(models.Model):
    _name = "app.release"
    _description = "发布管理"
    _order = "baseline_id, version_code desc, id"

    name = fields.Char(string="发布名称", compute="_compute_name", store=True)
    active = fields.Boolean(string="启用", default=True)

    # ---- 关联基线 ----
    baseline_id = fields.Many2one(
        "app.version.baseline", string="版本基线",
        required=True, ondelete="restrict", index=True,
    )
    platform = fields.Selection(
        related="baseline_id.platform", string="平台", store=True,
    )
    platform_version = fields.Char(
        related="baseline_id.platform_version", string="平台版本", store=True,
    )

    # ---- 版本信息 ----
    app_version = fields.Char(string="App 版本号", required=True, help="如：1.0.0, 2.3.1")
    version_code = fields.Integer(
        string="版本代码", required=True,
        help="必须与 APK 打包时的 versionCode 完全一致（build.gradle 中的 versionCode），整数递增，用于版本比较",
    )
    build_number = fields.Char(string="构建号", help="CI/CD 构建编号")

    # ---- 发布策略 ----
    is_force_update = fields.Boolean(
        string="强制更新",
        help="勾选后，低于此版本的 App 将强制要求更新",
    )
    min_support_version = fields.Char(
        string="最低支持版本",
        help="低于此版本的 App 将无法使用（需强制更新到此版本或更高）",
    )
    min_support_version_code = fields.Integer(
        string="最低支持版本代码",
        compute="_compute_min_support_version_code", store=True,
    )

    # ---- 依赖信息 ----
    dependency_ids = fields.Many2many(
        "app.release", "app_release_dependency_rel",
        "release_id", "dependency_id",
        string="发布依赖",
        help="此版本依赖的其他发布（如基础库版本）",
    )
    min_plugin_version = fields.Char(
        string="最低插件版本",
        help="此 App 版本要求的最低插件版本",
    )

    # ---- Release Note ----
    release_note = fields.Html(string="Release Note")
    release_summary = fields.Text(string="更新摘要", help="简短的更新要点列表")

    # ---- 状态与时间 ----
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
    revoke_date = fields.Datetime(string="撤回日期")
    revoke_reason = fields.Text(string="撤回原因")

    # ---- 附件 ----
    oss_config_id = fields.Many2one(
        "app.oss.config", string="OSS 配置",
        help="选择用于上传安装包的 OSS 配置，留空则使用默认启用的配置",
    )
    download_url = fields.Char(string="下载地址", readonly=True)
    package_file = fields.Binary(string="安装包文件", attachment=True)
    package_filename = fields.Char(string="安装包文件名")
    package_size = fields.Integer(string="包大小(字节)", compute="_compute_package_size", store=True)

    # ---- 资源关联 ----
    resource_ids = fields.Many2many(
        "app.resource", "app_release_resource_rel",
        "release_id", "resource_id",
        string="关联素材",
    )

    # ---- 备注 ----
    description = fields.Text(string="备注说明")

    @api.depends("baseline_id.platform", "baseline_id.platform_version", "app_version")
    def _compute_name(self):
        for record in self:
            platform_label = dict(
                record.baseline_id._fields["platform"].selection  # noqa
            ).get(record.platform, record.platform or "")
            record.name = f"{platform_label} {record.platform_version} - v{record.app_version}"

    @api.depends("min_support_version")
    def _compute_min_support_version_code(self):
        for record in self:
            if record.min_support_version:
                try:
                    parts = record.min_support_version.split(".")
                    code = 0
                    for i, p in enumerate(parts):
                        code += int(p) * (1000 ** (2 - i))
                    record.min_support_version_code = code
                except (ValueError, IndexError):
                    record.min_support_version_code = 0
            else:
                record.min_support_version_code = 0

    @api.depends("package_file")
    def _compute_package_size(self):
        for record in self:
            record.package_size = len(record.package_file) if record.package_file else 0

    def action_upload_to_oss(self):
        """手动上传安装包到 OSS 并回填 download_url"""
        self.ensure_one()
        if not self.package_file:
            raise UserError("请先上传安装包文件")
        # 不传 sub_path，路径完全由 OSS 配置的 base_path 决定
        url = self.env["app.oss.config"].upload_file(
            self.package_file,
            self.package_filename or "app_release.bin",
        )
        if url:
            self.download_url = url
        else:
            raise UserError("OSS 上传失败，请检查 OSS 配置")

    def write(self, vals):
        """已发布状态不允许编辑；草稿状态保留附件不删除"""
        for record in self:
            if record.state == "published" and not self.env.context.get("allow_revoke_write"):
                raise UserError("已发布的版本不允许编辑，请先撤回后再修改")
        return super().write(vals)

    @api.constrains("state", "baseline_id", "app_version")
    def _check_unique_published_version(self):
        """同一基线下的已发布版本号必须唯一"""
        for record in self:
            if record.state != "published":
                continue
            duplicate = self.search([
                ("id", "!=", record.id),
                ("baseline_id", "=", record.baseline_id.id),
                ("app_version", "=", record.app_version),
                ("state", "=", "published"),
            ], limit=1)
            if duplicate:
                raise UserError(
                    f"同一基线 ({record.baseline_id.name}) 下已存在已发布的版本 {record.app_version}，"
                    f"请先撤回旧版本或使用新的版本号"
                )

    def action_publish(self):
        """发布（先校验通过后再上传到 OSS）"""
        for record in self:
            if not record.package_file:
                raise UserError("请先上传安装包文件")
        self.write({
            "state": "published",
            "publish_date": fields.Datetime.now(),

        })
        for record in self:
            if not record.download_url:
                record.action_upload_to_oss()

    def action_revoke(self):
        """撤回"""
        return {
            "type": "ir.actions.act_window",
            "name": "撤回发布",
            "res_model": "app.release.revoke.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_release_id": self.id},  # noqa
        }

    def action_revoke_confirm(self, reason=""):
        """确认撤回"""
        self.with_context(allow_revoke_write=True).write({
            "state": "revoked",
            "revoke_date": fields.Datetime.now(),
            "revoke_reason": reason,
        })

    def action_to_testing(self):
        """转入测试"""
        self.write({"state": "testing"})


class AppReleaseRevokeWizard(models.TransientModel):
    _name = "app.release.revoke.wizard"
    _description = "撤回发布向导"

    release_id = fields.Many2one("app.release", string="发布", required=True)
    reason = fields.Text(string="撤回原因", required=True)

    def action_confirm(self):
        self.release_id.action_revoke_confirm(self.reason)
        return {"type": "ir.actions.act_window_close"}
