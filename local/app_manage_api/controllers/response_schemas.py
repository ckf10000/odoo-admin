# -*- coding: utf-8 -*-
"""app_manage_api 响应体 Pydantic 模型 — 严格对应 controller 中 json_response(data=...) 的实际结构"""
from typing import Optional, List
from pydantic import BaseModel, Field

"""
隐式绑定规则：
1.controller路由对应的方法名去掉 get_ 或 check_ 前缀
2.按 _ 分割，每个单词首字母大写
3.拼上 Body 或 Response
eg:
get_content_types → ContentTypesBody, ContentTypesResponse
get_search → SearchBody, SearchResponse
get_home_subcategories → HomeSubcategoriesBody, HomeSubcategoriesResponse
check_login → LoginBody, LoginResponse
"""


# ==================== 公共组件 ====================

class PluginUpdateInfo(BaseModel):
    """插件更新信息"""
    plugin_code: str = Field(..., description="插件编码")
    plugin_name: Optional[str] = Field(default=None, description="插件名称")
    current_version_code: int = Field(..., description="当前版本代码")
    latest_version_code: Optional[int] = Field(default=None, description="最新版本代码")
    latest_version: Optional[str] = Field(default=None, description="最新版本号")
    needs_update: bool = Field(default=False, description="是否需要更新")
    force_update: bool = Field(default=False, description="是否强制更新")
    distribution_mode: Optional[str] = Field(default=None, description="分发模式: inline/standalone/hot_update")
    require_restart: bool = Field(default=False, description="是否需要重启")
    download_url: Optional[str] = Field(default=None, description="下载地址")
    release_note: Optional[str] = Field(default=None, description="更新日志")
    package_size: Optional[int] = Field(default=None, description="包大小 (字节)")


class VersionCheckInfo(BaseModel):
    """版本更新信息"""
    force_update: bool = Field(default=False, description="是否强制更新")
    need_update: bool = Field(default=False, description="是否需要更新")
    latest_version: Optional[str] = Field(default=None, description="最新版本号")
    latest_version_code: Optional[int] = Field(default=None, description="最新版本代码")
    min_support_version: Optional[str] = Field(default=None, description="最低支持版本")
    update_url: Optional[str] = Field(default=None, description="更新下载地址")
    release_note: Optional[str] = Field(default="", description="更新日志")
    package_size: Optional[int] = Field(default=None, description="包大小 (字节)")
    baseline_name: Optional[str] = Field(default=None, description="基线名称")
    message: Optional[str] = Field(default=None, description="提示消息")


class ResourceInfo(BaseModel):
    """素材资源信息"""
    id: int = Field(..., description="资源 ID")
    name: str = Field(..., description="资源名称")
    resource_type: str = Field(..., description="资源类型")
    online_url: Optional[str] = Field(default=None, description="在线地址")
    resolution: Optional[str] = Field(default=None, description="分辨率")
    density: Optional[str] = Field(default=None, description="密度")
    file_size: Optional[int] = Field(default=None, description="文件大小 (字节)")
    force_update: bool = Field(default=False, description="是否强制更新")
    update_interval_hours: Optional[int] = Field(default=None, description="更新间隔 (小时)")


class LoginCheckInfo(BaseModel):
    """登录检查信息"""
    need_login: bool = Field(default=True, description="是否需要登录")
    message: Optional[str] = Field(default="", description="提示消息")


class CheckResult(BaseModel):
    """通用校验结果"""
    allowed: bool = Field(default=True, description="是否允许")
    message: Optional[str] = Field(default="OK", description="提示消息")


# ==================== 接口响应 ====================

class CheckLoginResponse(BaseModel):
    """检查登录状态响应"""
    data: LoginCheckInfo


class CheckVersionResponse(BaseModel):
    """检查版本更新响应"""
    data: VersionCheckInfo


class CheckPluginsResponse(BaseModel):
    """检查插件更新响应"""
    data: List[PluginUpdateInfo]


class CheckResourcesResponse(BaseModel):
    """检查资源更新响应"""
    data: List[ResourceInfo]


class CheckTerminalResponse(BaseModel):
    """检查终端响应"""
    data: CheckResult


class CheckChannelResponse(BaseModel):
    """检查渠道响应"""
    data: CheckResult
