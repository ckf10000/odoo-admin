# -*- coding: utf-8 -*-
"""app_manage_api 请求体 Pydantic 模型"""
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


class PluginInfo(BaseModel):
    """已安装插件信息"""
    plugin_code: str = Field(..., description="插件编码")
    version_code: int = Field(..., description="版本代码")


class CheckLoginBody(BaseModel):
    """检查登录状态"""
    app_version: Optional[str] = Field(default=None, description="App 版本号")
    app_version_code: Optional[int] = Field(default=0, description="App 版本代码")
    platform: Optional[str] = Field(default="", description="平台: ios / android / harmonyos")
    platform_version: Optional[str] = Field(default="", description="系统版本")
    terminal_model: Optional[str] = Field(default="", description="终端型号")
    channel_code: Optional[str] = Field(default="", description="渠道编码")
    user_id: Optional[int] = Field(default=None, description="用户 ID")
    installed_plugins: Optional[List[PluginInfo]] = Field(default_factory=list, description="已安装插件列表")


class CheckVersionBody(BaseModel):
    """检查版本更新"""
    app_version_code: Optional[int] = Field(default=0, description="App 版本代码")
    platform: Optional[str] = Field(default="", description="平台")
    platform_version: Optional[str] = Field(default="", description="系统版本")


class CheckPluginsBody(BaseModel):
    """检查插件更新"""
    platform: Optional[str] = Field(default="", description="平台")
    installed_plugins: Optional[List[PluginInfo]] = Field(default_factory=list, description="已安装插件列表")


class CheckResourcesBody(BaseModel):
    """检查资源更新"""
    platform: Optional[str] = Field(default="", description="平台")
    app_version_code: Optional[int] = Field(default=0, description="App 版本代码")


class CheckTerminalBody(BaseModel):
    """检查终端"""
    platform: Optional[str] = Field(default="", description="平台")
    terminal_model: Optional[str] = Field(default="", description="终端型号")


class CheckChannelBody(BaseModel):
    """检查渠道"""
    channel_code: Optional[str] = Field(default="", description="渠道编码")
    user_id: Optional[int] = Field(default=None, description="用户 ID")
