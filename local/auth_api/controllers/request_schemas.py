# -*- coding: utf-8 -*-
"""auth_api 请求体 Pydantic 模型"""
from typing import Optional
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


class TokenBody(BaseModel):
    """获取 Token（登录）"""
    username: str = Field(..., min_length=1, description="Odoo 用户名")
    password: str = Field(..., min_length=1, description="Odoo 密码")
    tenant: Optional[str] = Field(default=None, description="数据库名")


class RefreshBody(BaseModel):
    """刷新 Token"""
    grant_type: Optional[str] = Field(default="refresh_token", description="固定值")
    refresh_token: str = Field(..., min_length=1, description="登录返回的 refresh_token")


class RevokeBody(BaseModel):
    """撤销 Token"""
    token: str = Field(..., min_length=1, description="要撤销的 token")
    token_type_hint: Optional[str] = Field(default=None, description="可选提示: access_token / refresh_token")


class UserinfoBody(BaseModel):
    """获取用户信息 - 无业务参数"""
    pass


class LogoutBody(BaseModel):
    """登出 - 无业务参数"""
    pass


class ChangePasswordBody(BaseModel):
    """修改密码"""
    old_password: str = Field(..., min_length=1, description="当前密码")
    new_password: str = Field(..., min_length=6, description="新密码，长度 >= 6")
