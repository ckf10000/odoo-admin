# -*- coding: utf-8 -*-
{
    'name': "Odoo Redis",
    'summary': """
        Odoo Redis 扩展功能
       """,

    'description': """
        Odoo Redis 扩展功能, Redis 限制请求频率
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'external_dependencies': {
        'python': ['Crypto', 'redis'],  # 依赖库阿里云sdk，pip install aliyun-python-sdk-core-v3
    },

    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
    'auto_install': False,
    'application': True,
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
    ],
    'demo': [
        # 'demo/demo.xml',
    ],
}
