# -*- coding: utf-8 -*-
"""learn_api 响应体 Pydantic 模型"""
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


# ========== 公共组件 ==========

class ProcessInfo(BaseModel):
    """学习过程"""
    id: int = Field(..., description="过程关联 ID")
    name: str = Field(..., description="过程名称")
    code: str = Field(..., description="过程编码")
    sequence: int = Field(..., description="排序")


class ProfileInfo(BaseModel):
    """Profile 模板"""
    id: int = Field(..., description="Profile ID")
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(default="", description="描述")
    processes: List[ProcessInfo] = Field(default_factory=list, description="学习过程列表")


class GroupItem(BaseModel):
    """内容组条目"""
    id: int = Field(..., description="内容组 ID")
    name: str = Field(..., description="名称")
    sequence: int = Field(..., description="排序")
    description: Optional[str] = Field(default="", description="描述")
    section_count: int = Field(..., description="章节数")
    item_count: int = Field(..., description="条目总数")


class PaginatedGroups(BaseModel):
    """分页内容组列表"""
    list: List[GroupItem] = Field(default_factory=list, description="内容组列表")
    total: int = Field(..., description="总数")
    page_num: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


class SectionLine(BaseModel):
    """章节条目"""
    id: int = Field(..., description="条目 ID")
    sequence: int = Field(..., description="排序")
    content_type: str = Field(..., description="内容类型编码")
    score: float = Field(default=0.0, description="分值")


class SectionInfo(BaseModel):
    """内容组章节"""
    id: int = Field(..., description="章节 ID")
    name: str = Field(..., description="章节名称")
    sequence: int = Field(..., description="排序")
    content_type: str = Field(..., description="内容类型编码")
    score: float = Field(default=0.0, description="满分")
    lines: List[dict] = Field(default_factory=list, description="条目列表（动态结构）")


class ContentTypeInfo(BaseModel):
    """内容类型"""
    id: int = Field(..., description="类型 ID")
    name: str = Field(..., description="类型名称")
    code: str = Field(..., description="类型编码")
    storage_model: str = Field(..., description="存储模型")
    has_score: bool = Field(..., description="是否支持分值")
    sequence: int = Field(..., description="排序")
    description: Optional[str] = Field(default="", description="描述")


class WordResult(BaseModel):
    """搜索结果 - 单词"""
    id: int = Field(..., description="单词 ID")
    name: str = Field(..., description="单词")
    phonetic: Optional[str] = Field(default="", description="音标")
    meaning: Optional[str] = Field(default="", description="释义")
    difficulty: Optional[str] = Field(default="", description="难度")


class CharacterResult(BaseModel):
    """搜索结果 - 生字"""
    id: int = Field(..., description="生字 ID")
    name: str = Field(..., description="生字")
    pinyin: Optional[str] = Field(default="", description="拼音")
    meaning: Optional[str] = Field(default="", description="释义")
    strokes: Optional[int] = Field(default=0, description="笔画数")
    radical: Optional[str] = Field(default="", description="部首")
    difficulty: Optional[str] = Field(default="", description="难度")


class QuestionResult(BaseModel):
    """搜索结果 - 题目"""
    id: int = Field(..., description="题目 ID")
    question_type: str = Field(..., description="题目类型")
    stem: Optional[str] = Field(default="", description="题干")
    difficulty: Optional[str] = Field(default="", description="难度")


class SearchResults(BaseModel):
    """搜索结果"""
    keyword: str = Field(..., description="搜索关键词")
    results: dict = Field(default_factory=dict, description="搜索结果: {words, characters, questions}")


# ========== 接口响应 ==========

class ProfilesResponse(BaseModel):
    """获取全部 Profile 列表"""
    data: List[ProfileInfo]


class ProfileResponse(BaseModel):
    """获取单个 Profile"""
    data: ProfileInfo


class ContentTypesResponse(BaseModel):
    """获取内容类型列表"""
    data: List[ContentTypeInfo]


class GroupsResponse(BaseModel):
    """获取内容组列表"""
    data: PaginatedGroups


class GroupSectionsResponse(BaseModel):
    """获取内容组章节"""
    data: List[SectionInfo]


class SearchResponse(BaseModel):
    """全局搜索"""
    data: SearchResults


# ========== nav 接口响应 ==========

class DimNode(BaseModel):
    """维度树节点"""
    id: int = Field(..., description="维度值 ID")
    name: str = Field(..., description="维度值名称")
    code: str = Field(..., description="维度值编码")
    sequence: int = Field(..., description="排序")
    dim_type: str = Field(..., description="维度类型")
    dim_desc: str = Field(..., description="维度描述")
    children: List[dict] = Field(default_factory=list, description="子节点列表")
    selector_code: Optional[str] = Field(default=None, description="选择器编码（仅 subject 节点）")


class TabSelectorData(BaseModel):
    """选择器维度树数据"""
    default_condition: List[dict] = Field(default_factory=list, description="默认路径（第一条）")
    conditions: List[dict] = Field(default_factory=list, description="完整维度树")


class CategoryGroup(BaseModel):
    """首页分类分组"""
    category: dict = Field(..., description="{id, name, code}")
    subcategories: List[dict] = Field(default_factory=list, description="阶段列表")


class NavTab(BaseModel):
    """导航 Tab"""
    id: int = Field(..., description="Tab ID")
    code: str = Field(..., description="Tab 编码")
    name: str = Field(..., description="Tab 名称")
    nav_icon: Optional[str] = Field(default=None, description="导航图标（base64）")
    nav_icon_active: Optional[str] = Field(default=None, description="激活态图标（base64）")
    is_home: bool = Field(default=False, description="是否为首页 Tab")
    sequence: int = Field(..., description="排序")


class HomeSubcategoriesResponse(BaseModel):
    """首页分类聚合"""
    data: List[CategoryGroup]


class TabSelectorResponse(BaseModel):
    """选择器维度树"""
    data: TabSelectorData


class NavTabsResponse(BaseModel):
    """底部导航 Tab 列表"""
    data: List[NavTab]
