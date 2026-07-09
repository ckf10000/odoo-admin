# -*- coding: utf-8 -*-
{
    'name': "App Manage API - 移动端校验接口",

    'summary': "提供移动端 App 登录校验、版本检查、插件检查、素材检查等 REST API",

    'description': """
        App 管理 REST API
        =================
        提供以下接口供移动端调用：
        - 登录校验（是否需要强制更新）
        - 版本检查（最新版本、强制更新标识）
        - 插件检查（是否需要更新插件、分发模式）
        - 素材检查（是否需要更新素材）
        - 终端校验（是否在白名单内）
        - 渠道校验（是否在渠道白名单内）
    """,

    'author': "ckf10000@sina.com",
    'website': "https://gitee.com/mfkifhss/odoo-admin",

    'category': 'Customizations/AppManage',
    'version': '17.0.0.1',

    'depends': ['app_manage_core', 'common_lib', 'auth_api'],

    'data': [],

    'application': True,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}
