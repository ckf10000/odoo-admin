# -*- coding: utf-8 -*-
{
    'name': "Learn Interact - 学习交互",

    'summary': "学习交互模块：试卷答题、批阅、成绩、错题本、收藏、批注、笔记",

    'description': """
        学习交互模块
        ================
        提供学习过程中的交互功能：
        - 试卷/练习册答题与自动批阅
        - 成绩管理与历史记录
        - 错题本
        - 教材收藏
        - 批注与笔记
        - 评论与评分
    """,

    'author': "HLKJ",
    'website': "https://www.hlgjzn.com/",

    'category': 'Customizations/Learn',
    'version': '17.0.0.1',

    'depends': ['base', 'learn_core'],

    'data': [
        'security/ir.model.access.csv',
        'security/learn_security.xml',
        'views/learn_exam_views.xml',
        'views/learn_note_views.xml',
        'views/learn_menus.xml',
    ],

    'application': False,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}
