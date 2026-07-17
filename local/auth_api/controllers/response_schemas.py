# -*- coding: utf-8 -*-
"""auth_api 响应体 Pydantic 模型 — 严格对应 controller 中 json_response(data=...) 的实际结构"""
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


# ==================== 公共组件 ====================

class TokenData(BaseModel):
    """Token 响应数据"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(default=7200, description="过期时间（秒）")
    refresh_token: str = Field(..., description="刷新令牌")
    scope: Optional[str] = Field(default=None, description="作用域")


class UserInfo(BaseModel):
    """用户信息"""
    id: int = Field(..., description="用户 ID")
    login: str = Field(..., description="登录名")
    name: str = Field(..., description="显示名称")
    email: Optional[str] = Field(default=None, description="邮箱")
    lang: Optional[str] = Field(default=None, description="语言")
    tz: Optional[str] = Field(default=None, description="时区")
    company_id: Optional[int] = Field(default=None, description="公司 ID")
    company_name: Optional[str] = Field(default=None, description="公司名称")


class RevokeData(BaseModel):
    """撤销 Token 响应数据"""
    revoked: bool = Field(default=True, description="是否已撤销")


class LogoutData(BaseModel):
    """登出响应数据"""
    revoked_count: int = Field(default=0, description="撤销的 Token 数量")


# ==================== 接口响应 ====================

class TokenResponse(BaseModel):
    """登录获取 Token 响应"""
    data: TokenData


class RefreshResponse(BaseModel):
    """刷新 Token 响应"""
    data: TokenData


class RevokeResponse(BaseModel):
    """撤销 Token 响应"""
    data: RevokeData


class UserinfoResponse(BaseModel):
    """获取用户信息响应"""
    data: UserInfo


class LogoutResponse(BaseModel):
    """登出响应"""
    data: LogoutData


class ChangePasswordResponse(BaseModel):
    """修改密码响应（仅 message，无 data 字段）"""
    pass
