# -*- coding: utf-8 -*-
"""维度链常量

selector 树构建的维度顺序，依次为：
    category → stage → class → region → version → year → semester → subject

三元组: (字段名, dim_type, dim_desc)
- 字段名：learn.selector 模型中的字段名（Many2one 为 xxx_id，Many2many 为 xxx_ids）
- dim_type：对外暴露的维度类型标识
- dim_desc：中文描述

数据约束：同一前缀路径下，某维度必须全配或全缺，不允许部分有部分无。
"""
DIM_CHAIN = [
    ("category_id", "category", "类别"),
    ("stage_id", "stage", "阶段"),
    ("class_id", "class", "年级"),
    ("region_ids", "region", "地区"),
    ("version_id", "version", "版本"),
    ("year_id", "year", "年份"),
    ("semester_id", "semester", "学期"),
    ("subject_id", "subject", "科目"),
]
