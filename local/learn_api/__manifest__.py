# -*- coding: utf-8 -*-
{
    'name': "Learn API - 学习平台 API",

    'summary': "学习平台 REST API 接口，供 Android/iOS 客户端调用",

    'description': """
        学习平台 API 模块
        ================
        提供完整的 REST API 接口：
        - 分类树查询
        - 内容列表/详情
        - 试卷答题与批阅
        - 成绩查询
        - 错题本
        - 收藏/批注/笔记/评论
    """,

    'author': "ckf10000@sina.com",
    'website': "https://gitee.com/mfkifhss/odoo-admin",

    'category': 'Customizations/Learn',
    'version': '17.0.0.1',

    'depends': ['base', 'common_lib', 'learn_core', 'learn_interact', 'auth_api'],

    'data': [],

    'application': True,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}
