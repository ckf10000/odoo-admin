# -*- coding: utf-8 -*-
{
    'name': "Learn Core - 学习平台核心",

    'summary': "学习平台核心模块：分类体系、教材、试卷、练习册、视频管理",

    'description': """
        学习平台核心模块
        ================
        提供灵活可扩展的分类树结构，支持：
        - 教材 (Textbook)
        - 试卷 (Exam Paper)  
        - 练习册 (Workbook)
        - 视频 (Video)
        等学习内容的管理。
    """,

    'author': "ckf10000@sina.com",
    'website': "https://gitee.com/mfkifhss/odoo-admin",

    'category': 'Customizations/Learn',
    'version': '17.0.1.1',

    'depends': ['base', 'web', 'mail'],

    'data': [
        'security/ir.model.access.csv',
        'views/learn_dim_views.xml',
        'views/learn_word_views.xml',
        'views/learn_menus.xml',
        'views/learn_process_views.xml',
        'views/learn_word_source_views.xml',
        'views/learn_group_views.xml',
        'views/learn_content_type_views.xml',
        'views/learn_selector_views.xml',
        'views/learn_media_views.xml',
        'views/learn_article_views.xml',
        'views/learn_character_views.xml',
        'views/learn_subject_profile_views.xml',
        'views/learn_content_views.xml',
        'data/learn_dim_category_data.xml',
        'data/learn_dim_stage_data.xml',
        'data/learn_dim_klass_data.xml',
        'data/learn_dim_region_data.xml',
        'data/learn_dim_subject_data.xml',
        'data/learn_dim_year_data.xml',
        'data/learn_dim_semester_data.xml',
        'data/learn_dim_version_data.xml',
        'data/learn_content_type_data.xml',
        'data/learn_process_data.xml',
        'data/learn_subject_profile_data.xml',
        'data/learn_selector_data.xml',
        'data/learn_word_source_data_phonics.xml',
        'data/learn_word_data.xml',
        'data/learn_word_group_data_phonics.xml',
        'data/learn_word_group_data_g5_english.xml',
        'data/learn_question_data_g5_english.xml',
        'data/learn_material_data_g5_english.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'learn_core/static/src/js/pdf_viewer.js',
            'learn_core/static/src/scss/learn_core.scss',
            'learn_core/static/src/xml/pdf_viewer.xml',
        ],
    },

    'application': True,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}
