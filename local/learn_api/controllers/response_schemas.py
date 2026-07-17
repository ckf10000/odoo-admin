# -*- coding: utf-8 -*-
"""learn_api 响应体 Pydantic 模型 — 严格对应 controller 中 json_response(data=...) 的实际结构"""
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

class PosInfo(BaseModel):
    """词性"""
    id: int = Field(..., description="词性 ID")
    name: str = Field(..., description="词性名称")
    code: str = Field(..., description="词性编码")


class WordResult(BaseModel):
    """搜索结果 - 单词"""
    id: int = Field(..., description="单词 ID")
    name: str = Field(..., description="单词")
    phonetic: str = Field(default="", description="音标")
    meaning: str = Field(default="", description="中文释义")
    difficulty: str = Field(..., description="难度: easy/medium/hard")
    pos: List[PosInfo] = Field(default_factory=list, description="词性列表")


class CharacterResult(BaseModel):
    """搜索结果 - 生字"""
    id: int = Field(..., description="生字 ID")
    name: str = Field(..., description="生字")
    pinyin: str = Field(default="", description="拼音")
    meaning: str = Field(default="", description="释义")
    strokes: int = Field(default=0, description="笔画数")
    radical: str = Field(default="", description="部首")
    difficulty: str = Field(..., description="难度: easy/medium/hard")


class QuestionResult(BaseModel):
    """搜索结果 - 题目"""
    id: int = Field(..., description="题目 ID")
    question_type: str = Field(...,
                               description="题目类型: single_choice/multi_choice/fill_blank/true_false/calculation/essay")
    stem: str = Field(default="", description="题干")
    difficulty: str = Field(..., description="难度: easy/medium/hard")


class SearchData(BaseModel):
    """搜索结果数据"""
    keyword: str = Field(..., description="搜索关键词")
    results: dict = Field(default_factory=dict,
                          description="搜索结果，根据 scope 不同包含 words/characters/questions 中的一个或多个")


class ProcessInfo(BaseModel):
    """学习过程"""
    id: int = Field(..., description="过程关联 ID (selector.process 的 id)")
    name: str = Field(..., description="过程名称")
    code: str = Field(..., description="过程编码")
    sequence: int = Field(..., description="排序")


class ProfileInfo(BaseModel):
    """Profile 模板"""
    id: int = Field(..., description="Profile ID")
    name: str = Field(..., description="模板名称")
    description: str = Field(default="", description="描述")
    processes: List[ProcessInfo] = Field(default_factory=list, description="学习过程列表")


class SelectorProcessItem(BaseModel):
    """选择器-过程项（第一个过程附带内容组）"""
    id: int = Field(..., description="关联 ID (selector.process)")
    process_id: int = Field(..., description="过程 ID")
    process_name: str = Field(..., description="过程名称")
    process_code: str = Field(..., description="过程编码")
    sequence: int = Field(..., description="排序")
    groups: Optional[dict] = Field(default=None, description="内容组分页数据 (仅第一个过程有)")


class ContentTypeInfo(BaseModel):
    """内容类型"""
    id: int = Field(..., description="类型 ID")
    name: str = Field(..., description="类型名称")
    code: str = Field(..., description="类型编码")
    storage_model: str = Field(..., description="存储模型: learn.phrase/learn.question/learn.media/learn.article")
    has_score: bool = Field(..., description="是否支持分值")
    sequence: int = Field(..., description="排序")
    description: str = Field(default="", description="描述")


class GroupItem(BaseModel):
    """内容组概要"""
    id: int = Field(..., description="内容组 ID")
    name: str = Field(..., description="名称")
    sequence: int = Field(..., description="排序")
    description: str = Field(default="", description="描述")
    section_count: int = Field(..., description="章节数")
    item_count: int = Field(..., description="条目总数")


class GroupListData(BaseModel):
    """内容组分页列表"""
    list: List[GroupItem] = Field(default_factory=list, description="内容组列表")
    total: int = Field(..., description="总数")
    page_num: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


class SectionLineItem(BaseModel):
    """章节条目（动态结构，根据 res_model 不同包含 word/character/phrase/question/media/article）"""
    id: int = Field(..., description="条目 ID")
    sequence: int = Field(..., description="排序")
    content_type: str = Field(..., description="内容类型编码")
    score: float = Field(default=0.0, description="分值")
    word: Optional[dict] = Field(default=None, description="单词数据 (res_model=learn.word 时)")
    character: Optional[dict] = Field(default=None, description="生字数据 (res_model=learn.character 时)")
    phrase: Optional[dict] = Field(default=None, description="字词桥接数据 (res_model=learn.phrase 时)")
    question: Optional[dict] = Field(default=None, description="题目数据 (res_model=learn.question 时)")
    media: Optional[dict] = Field(default=None, description="媒体数据 (res_model=learn.media 时)")
    article: Optional[dict] = Field(default=None, description="图文数据 (res_model=learn.article 时)")


class SectionInfo(BaseModel):
    """内容组章节"""
    id: int = Field(..., description="章节 ID")
    name: str = Field(..., description="章节名称")
    sequence: int = Field(..., description="排序")
    content_type: str = Field(..., description="内容类型编码")
    score: float = Field(default=0.0, description="本章节满分")
    lines: List[SectionLineItem] = Field(default_factory=list, description="条目列表")


class CategoryInfo(BaseModel):
    """分类信息"""
    id: int = Field(..., description="分类 ID")
    name: str = Field(..., description="分类名称")
    code: str = Field(..., description="分类编码")


class SubcategoryInfo(BaseModel):
    """子分类（阶段）"""
    id: int = Field(..., description="阶段 ID")
    name: str = Field(..., description="阶段名称")
    code: str = Field(..., description="阶段编码")
    sequence: int = Field(..., description="排序")


class HomeCategoryGroup(BaseModel):
    """首页分类分组"""
    category: CategoryInfo
    subcategories: List[SubcategoryInfo] = Field(default_factory=list, description="阶段列表")


class TabSelectorData(BaseModel):
    """选择器维度树数据"""
    default_condition: List[dict] = Field(default_factory=list, description="默认路径（第一条完整路径）")
    conditions: List[dict] = Field(default_factory=list, description="完整维度树（递归结构）")


class NavTab(BaseModel):
    """导航 Tab"""
    id: int = Field(..., description="Tab ID (0 为全部)")
    code: str = Field(..., description="Tab 编码 (all 为全部)")
    name: str = Field(..., description="Tab 名称")
    nav_icon: Optional[str] = Field(default=None, description="导航图标 (base64)")
    nav_icon_active: Optional[str] = Field(default=None, description="激活态图标 (base64)")
    is_home: bool = Field(default=False, description="是否为首页 Tab")
    sequence: int = Field(..., description="排序")


# ==================== 接口响应 (data 字段) ====================

class SearchResponse(BaseModel):
    """全局搜索响应"""
    data: SearchData


class ContentTypesResponse(BaseModel):
    """内容类型列表响应"""
    data: List[ContentTypeInfo]


class GroupsResponse(BaseModel):
    """内容组列表响应"""
    data: GroupListData


class GroupSectionsResponse(BaseModel):
    """内容组章节响应"""
    data: List[SectionInfo]


class ProfilesResponse(BaseModel):
    """全部 Profile 列表响应"""
    data: List[ProfileInfo]


class ProfileResponse(BaseModel):
    """单个 Profile 响应"""
    data: ProfileInfo


class SelectorProcessesResponse(BaseModel):
    """选择器-过程列表响应"""
    data: List[SelectorProcessItem]


class HomeSubcategoriesResponse(BaseModel):
    """首页分类聚合响应"""
    data: List[HomeCategoryGroup]


class TabSelectorResponse(BaseModel):
    """选择器维度树响应"""
    data: TabSelectorData


class NavTabsResponse(BaseModel):
    """导航 Tab 列表响应"""
    data: List[NavTab]
