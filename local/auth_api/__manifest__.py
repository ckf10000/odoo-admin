# -*- coding: utf-8 -*-
{
    'name': "Auth API - OAuth2.0 第三方认证",
    'summary': "OAuth2.0 认证服务，支持 App/第三方客户端登录",
    'description': """
        为 Android/iOS App 或第三方客户端提供 OAuth2.0 认证接口。
        
        支持：
        - OAuth2.0 Password Grant (密码模式)
        - OAuth2.0 Refresh Token (令牌刷新)
        - Bearer Token 认证中间件
        - 客户端注册与管理
        - Token 过期自动清理
        - 登录日志记录
    """,
    'author': "ckf10000@sina.com",
    'website': "https://gitee.com/mfkifhss/odoo-admin",
    'category': 'Customizations/auth_api',
    'version': '17.0.0.1',
    'depends': ['base', 'web', 'common_lib'],
    'data': [
        'security/ir.model.access.csv',
        'security/auth_api_security.xml',
        'data/auth_api_data.xml',
        'views/auth_api_views.xml',
        'views/auth_api_menus.xml',
    ],
    'application': True,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}
