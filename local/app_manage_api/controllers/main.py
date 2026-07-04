# -*- coding: utf-8 -*-
"""
App 生命周期管理 REST API

接口前缀: /api/app/v1/

认证方式（get_user 自动识别）:
  1. Bearer Token   - Header: Authorization: Bearer <access_token>
  2. Session Cookie  - 浏览器 Web 登录

响应格式:
  {
    "success": true/false,
    "data": {...},
    "message": "...",
    "error": "..."  // 仅在失败时
  }
"""
import logging
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
from odoo.addons.learn_common.common import json_response, error_response, get_user, get_json  # noqa

_logger = logging.getLogger(__name__)


# ==================== 登录校验 API ====================

class AppCheckController(http.Controller):
    """移动端 App 登录时调用的综合校验接口

    移动端在以下时机调用:
    1. App 冷启动 / 登录时 → 调用 /check/login
    2. 加载插件时 → 调用 /check/plugins
    3. 检查素材更新 → 调用 /check/resources
    """

    @http.route("/api/v1/app/check/login", type="http", auth="public", methods=["POST"], csrf=False)
    def check_login(self, **kwargs):  # noqa
        """App 登录综合校验

        移动端在启动/登录时调用，一次性返回所有需要校验的结果。

        Request Body (JSON):
        {
            "app_version": "1.0.0",          // App 版本号
            "app_version_code": 1000,         // App 版本代码（整数）
            "platform": "android",            // 平台: ios/android/harmonyos
            "platform_version": "14",         // 系统版本，如 "iOS 18.0", "Android 14"
            "terminal_model": "SM-S9280",     // 终端型号
            "channel_code": "huawei",         // 渠道编码
            "user_id": 1,                     // 用户 ID（可选，用于渠道白名单校验）
            "installed_plugins": [            // 已安装的插件列表
                {"plugin_code": "ocr", "version_code": 100},
                {"plugin_code": "push", "version_code": 200}
            ]
        }

        Response:
        {
            "success": true,
            "data": {
                "force_update": false,                    // 是否需要强制更新
                "need_update": true,                      // 是否需要更新 App
                "latest_version": "1.2.0",               // 最新版本号
                "latest_version_code": 1200,             // 最新版本代码
                "update_url": "https://...",             // 下载地址
                "release_note": "...",                    // 更新说明
                "terminal_allowed": true,                 // 终端是否在白名单内
                "terminal_message": "OK",                 // 终端校验信息
                "channel_allowed": true,                  // 渠道是否允许
                "channel_message": "OK",                  // 渠道校验信息
                "plugins": [                              // 需要更新的插件
                    {
                        "plugin_code": "ocr",
                        "needs_update": true,
                        "force_update": false,
                        "latest_version_code": 150,
                        "distribution_mode": "optional"
                    }
                ],
                "resources": [                            // 需要更新的素材
                    {
                        "resource_name": "app_icon",
                        "resource_type": "app_icon",
                        "online_url": "https://...",
                        "force_update": true
                    }
                ]
            }
        }
        """
        try:
            get_user()
            data = get_json()
            _log_check_request(data)

            app_version_code = data.get("app_version_code", 0)
            platform = data.get("platform", "")
            platform_version = data.get("platform_version", "")
            terminal_model = data.get("terminal_model", "")
            channel_code = data.get("channel_code", "")
            user_id = data.get("user_id")
            installed_plugins = data.get("installed_plugins", [])

            # 1. 终端校验
            terminal_allowed, terminal_message = self._check_terminal(platform, terminal_model)

            # 2. 渠道校验
            channel_allowed, channel_message = self._check_channel(channel_code, user_id)

            # 3. 版本校验（检查是否需要更新）
            version_info = self._check_version(platform, platform_version, app_version_code)

            # 4. 插件校验
            plugin_info = self._check_plugins(platform, installed_plugins)

            # 5. 素材校验
            resource_info = self._check_resources(platform, app_version_code)

            return json_response(data={
                "force_update": version_info.get("force_update", False),
                "need_update": version_info.get("need_update", False),
                "latest_version": version_info.get("latest_version"),
                "latest_version_code": version_info.get("latest_version_code"),
                "update_url": version_info.get("update_url"),
                "release_note": version_info.get("release_note"),
                "terminal_allowed": terminal_allowed,
                "terminal_message": terminal_message,
                "channel_allowed": channel_allowed,
                "channel_message": channel_message,
                "plugins": plugin_info,
                "resources": resource_info,
            })

        except AccessDenied as e:
            return error_response(e, 403)
        except Exception as e:
            _logger.exception("App check/login error")
            return error_response(e, 500)

    @http.route("/api/v1/app/check/version", type="http", auth="public", methods=["POST"], csrf=False)
    def check_version(self, **kwargs):  # noqa
        """单独检查版本更新

        Request Body (JSON):
        {
            "app_version_code": 1000,
            "platform": "android",
            "platform_version": "14"
        }
        """
        try:
            get_user()
            data = get_json()
            app_version_code = data.get("app_version_code", 0)
            platform = data.get("platform", "")
            platform_version = data.get("platform_version", "")

            version_info = self._check_version(platform, platform_version, app_version_code)
            return json_response(data=version_info)

        except AccessDenied as e:
            return error_response(e, 403)
        except Exception as e:
            _logger.exception("App check/version error")
            return error_response(e, 500)

    @http.route("/api/v1/app/check/plugins", type="http", auth="public", methods=["POST"], csrf=False)
    def check_plugins(self, **kwargs):  # noqa
        """单独检查插件更新

        Request Body (JSON):
        {
            "platform": "android",
            "installed_plugins": [
                {"plugin_code": "ocr", "version_code": 100}
            ]
        }
        """
        try:
            get_user()
            data = get_json()
            platform = data.get("platform", "")
            installed_plugins = data.get("installed_plugins", [])

            plugin_info = self._check_plugins(platform, installed_plugins)
            return json_response(data=plugin_info)

        except AccessDenied as e:
            return error_response(e, 403)
        except Exception as e:
            _logger.exception("App check/plugins error")
            return error_response(e, 500)

    @http.route("/api/v1/app/check/resources", type="http", auth="public", methods=["POST"], csrf=False)
    def check_resources(self, **kwargs):  # noqa
        """单独检查素材更新

        Request Body (JSON):
        {
            "platform": "android",
            "app_version_code": 1000
        }
        """
        try:
            get_user()
            data = get_json()
            platform = data.get("platform", "")
            app_version_code = data.get("app_version_code", 0)

            resource_info = self._check_resources(platform, app_version_code)
            return json_response(data=resource_info)

        except AccessDenied as e:
            return error_response(e, 403)
        except Exception as e:
            _logger.exception("App check/resources error")
            return error_response(e, 500)

    @http.route("/api/v1/app/check/terminal", type="http", auth="public", methods=["POST"], csrf=False)
    def check_terminal(self, **kwargs):  # noqa
        """单独校验终端

        Request Body (JSON):
        {
            "platform": "android",
            "terminal_model": "SM-S9280"
        }
        """
        try:
            get_user()
            data = get_json()
            platform = data.get("platform", "")
            terminal_model = data.get("terminal_model", "")

            allowed, message = self._check_terminal(platform, terminal_model)
            return json_response(data={
                "allowed": allowed,
                "message": message,
            })

        except AccessDenied as e:
            return error_response(e, 403)
        except Exception as e:
            _logger.exception("App check/terminal error")
            return error_response(e, 500)

    @http.route("/api/v1/app/check/channel", type="http", auth="public", methods=["POST"], csrf=False)
    def check_channel(self, **kwargs):  # noqa
        """单独校验渠道

        Request Body (JSON):
        {
            "channel_code": "huawei",
            "user_id": 1
        }
        """
        try:
            get_user()
            data = get_json()
            channel_code = data.get("channel_code", "")
            user_id = data.get("user_id")

            allowed, message = self._check_channel(channel_code, user_id)
            return json_response(data={
                "allowed": allowed,
                "message": message,
            })

        except AccessDenied as e:
            return error_response(e, 403)
        except Exception as e:
            _logger.exception("App check/channel error")
            return error_response(e, 500)

    # ==================== 内部校验方法 ====================

    def _check_terminal(self, platform, terminal_model):  # noqa
        """终端白名单校验"""
        if not platform or not terminal_model:
            return True, "OK"  # 未传则跳过

        allowed, message = request.env["app.terminal"].sudo().check_terminal_allowed(
            platform, terminal_model
        )
        return allowed, message

    def _check_channel(self, channel_code, user_id=None):  # noqa
        """渠道白名单校验"""
        if not channel_code:
            return True, "OK"

        channel = request.env["app.channel"].sudo().search([
            ("channel_code", "=", channel_code),
            ("active", "=", True),
        ], limit=1)

        if not channel:
            return False, f"渠道 {channel_code} 不存在或已禁用"

        # 白名单校验
        if channel.use_whitelist and user_id:
            if channel.whitelist_mode == "user":
                if user_id not in channel.whitelist_user_ids.ids:
                    return False, f"用户不在渠道 {channel_code} 的白名单内"
            elif channel.whitelist_mode == "organization":
                user = request.env["res.users"].sudo().browse(user_id)
                if user.exists() and user.partner_id.id not in channel.whitelist_partner_ids.ids:
                    return False, f"用户所属组织不在渠道 {channel_code} 的白名单内"

        return True, "OK"

    def _check_version(self, platform, platform_version, app_version_code):  # noqa
        """版本更新校验"""
        # 查找匹配的基线
        baseline_domain = [
            ("platform", "=", platform),
            ("active", "=", True),
            ("is_deprecated", "=", False),
        ]
        if platform_version:
            baseline_domain.append(("platform_version", "=", platform_version))

        baseline = request.env["app.version.baseline"].sudo().search(
            baseline_domain, limit=1
        )

        if not baseline:
            return {
                "force_update": False,
                "need_update": False,
                "latest_version": None,
                "latest_version_code": None,
                "message": "未找到匹配的版本基线",
            }

        # 查找该基线下的最新已发布版本
        latest_release = request.env["app.release"].sudo().search([
            ("baseline_id", "=", baseline.id),
            ("state", "=", "published"),
        ], order="version_code desc", limit=1)

        if not latest_release:
            return {
                "force_update": False,
                "need_update": False,
                "latest_version": None,
                "latest_version_code": None,
                "message": "该基线暂无已发布版本",
            }

        need_update = latest_release.version_code > app_version_code
        force_update = latest_release.is_force_update and need_update

        # 检查最低支持版本
        if latest_release.min_support_version_code and app_version_code < latest_release.min_support_version_code:
            force_update = True
            need_update = True

        return {
            "force_update": force_update,
            "need_update": need_update,
            "latest_version": latest_release.app_version,
            "latest_version_code": latest_release.version_code,
            "min_support_version": latest_release.min_support_version,
            "update_url": latest_release.download_url,
            "release_note": latest_release.release_summary or "",
            "package_size": latest_release.package_size,
            "baseline_name": baseline.name,
        }

    def _check_plugins(self, platform, installed_plugins):  # noqa
        """插件更新校验"""
        results = []

        for p in installed_plugins:
            plugin_code = p.get("plugin_code")
            current_version_code = p.get("version_code", 0)

            info = request.env["app.plugin"].sudo().get_plugin_info_for_check(
                plugin_code, current_version_code
            )

            if info.get("exists"):
                results.append({
                    "plugin_code": plugin_code,
                    "plugin_name": info.get("plugin_name"),
                    "current_version_code": current_version_code,
                    "latest_version_code": info.get("latest_version_code"),
                    "latest_version": info.get("latest_version"),
                    "needs_update": info.get("needs_update"),
                    "force_update": info.get("force_update"),
                    "distribution_mode": info.get("distribution_mode"),
                    "require_restart": info.get("require_restart"),
                    "download_url": info.get("download_url"),
                    "release_note": info.get("release_note"),
                    "package_size": info.get("package_size"),
                })

        return results

    def _check_resources(self, platform, app_version_code):  # noqa
        """素材更新校验"""
        domain = [
            ("active", "=", True),
            "|",
            ("platform", "=", platform),
            ("platform", "=", "all"),
        ]

        resources = request.env["app.resource"].sudo().search(domain)

        results = []
        for r in resources:
            # 检查版本限制
            if r.min_app_version_code and app_version_code < r.min_app_version_code:
                continue
            if r.baseline_id and r.baseline_id.platform != platform:
                continue

            results.append({
                "id": r.id,
                "name": r.name,
                "resource_type": r.resource_type,
                "online_url": r.online_url,
                "resolution": r.resolution,
                "density": r.density,
                "file_size": r.file_size,
                "force_update": r.is_force_update,
                "update_interval_hours": r.update_interval_hours,
            })

        return results


def _log_check_request(data):
    """记录校验请求日志（可选）"""
    _logger.info(
        "App check request: platform=%s, version=%s, terminal=%s, channel=%s",
        data.get("platform"),
        data.get("app_version"),
        data.get("terminal_model"),
        data.get("channel_code"),
    )
