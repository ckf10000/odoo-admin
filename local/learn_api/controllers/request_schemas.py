# -*- coding: utf-8 -*-
"""learn_api 模块请求体 Pydantic 模型"""
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


class ContentTypesBody(BaseModel):
    """获取所有启用的内容类型 - 无业务参数"""
    pass


class SearchBody(BaseModel):
    """全局搜索"""
    keyword: str = Field(..., min_length=1, description="搜索关键词")
    scope: Optional[str] = Field(default="all", description="搜索范围: all / word / character / question")
    page_num: Optional[int] = Field(default=1, ge=1, description="页码")
    page_size: Optional[int] = Field(default=20, ge=1, le=50, description="每页数量")


class HomeSubcategoriesBody(BaseModel):
    """首页分类聚合"""
    category_code: Optional[str] = Field(default=None, description="分类编码，不传返回所有")


class TabSelectorBody(BaseModel):
    """选择器维度树"""
    category_code: Optional[str] = Field(default=None, description="分类编码")
    sub_category_code: Optional[str] = Field(default="", description="阶段编码（需同时传 category_code）")


class NavTabsBody(BaseModel):
    """底部导航 Tab 列表 - 无业务参数"""
    pass


class SelectorProcessesBody(BaseModel):
    """选择器下绑定的过程列表"""
    selector_code: str = Field(..., min_length=1, description="选择器编码")
    page_num: Optional[int] = Field(default=1, ge=1, description="页码")
    page_size: Optional[int] = Field(default=10, ge=1, le=50, description="每页数量")


class ProfilesBody(BaseModel):
    """获取全部 Profile 列表 - 无业务参数"""
    pass


class ProfileBody(BaseModel):
    """根据 selector_code 获取单个 Profile"""
    selector_code: str = Field(..., min_length=1, description="选择器编码")


class GroupsBody(BaseModel):
    """根据 selector_code 和 process_code 获取内容组列表"""
    selector_code: str = Field(..., min_length=1, description="选择器编码")
    process_code: str = Field(..., min_length=1, description="学习过程编码")
    page_num: Optional[int] = Field(default=1, ge=1, description="页码")
    page_size: Optional[int] = Field(default=10, ge=1, le=50, description="每页数量")


class GroupSectionsBody(BaseModel):
    """获取内容组下所有章节 - 无业务参数"""
    pass
