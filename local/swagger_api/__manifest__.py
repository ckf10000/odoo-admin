# -*- coding: utf-8 -*-
{
    'name': "Swagger API - OpenAPI 文档",

    'summary': "自动为所有 REST API 接口生成 Swagger / OpenAPI 3.0 文档",

    'description': """
        Swagger / OpenAPI 3.0 文档
        ==========================
        提供以下能力：
        - /api/swagger.json   → 自动生成 OpenAPI 3.0 规范的 JSON 文档
        - /api/swagger         → Swagger UI 交互式页面
        - /api/swagger/redoc    → ReDoc 文档页面

        自动扫描所有已安装模块中前缀为 /api/ 的路由。
    """,

    'author': "ckf10000@sina.com",
    'website': "https://gitee.com/mfkifhss/odoo-admin",

    'category': 'Customizations/Swagger API',
    'version': '17.0.0.1',

    'depends': ['base'],

    'data': [],

    'application': True,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}
