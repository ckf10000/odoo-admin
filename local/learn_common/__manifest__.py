# -*- coding: utf-8 -*-
{
    'name': "Learn Common - 学习平台公共模块",

    'summary': "学习平台公共工具模块，提供统一 JSON 响应、认证、图片编码等通用能力",

    'description': """
        学习平台公共模块
        ================
        提供以下通用能力：
        - 统一 JSON 响应格式
        - 多方式用户认证（Bearer Token / Session）
        - Base64 图片编码
    """,

    'author': "ckf10000@sina.com",
    'website': "https://gitee.com/mfkifhss/odoo-admin",

    'category': 'Customizations/Learn',
    'version': '17.0.0.1',

    'depends': ['base', 'auth_api'],

    'data': [],

    'application': False,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}
