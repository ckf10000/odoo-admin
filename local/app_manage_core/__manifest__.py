# -*- coding: utf-8 -*-
{
    'name': "App Manage Core - 移动端生命周期管理",

    'summary': "App版本管理、插件管理、渠道管理、终端管理",

    'description': """
        移动端 App 生命周期管理核心模块
        =================================
        提供以下功能：
        - App 版本基线库（iOS/Android/HarmonyOS 平台版本管理）
        - 发布管理（Release Note、强制更新、发布依赖）
        - 版本素材管理（离线/在线 icon、启动图等）
        - 渠道管理（渠道商、渠道白名单）
        - 终端管理（设备型号白名单）
        - App 插件管理（上传、分发策略、强制/非强制）
    """,

    'author': "ckf10000@sina.com",
    'website': "https://gitee.com/mfkifhss/odoo-admin",

    'category': 'Customizations/AppManage',
    'version': '17.0.0.1',

    'depends': ['base', 'web', 'mail'],

    'data': [
        'security/ir.model.access.csv',
        'views/app_version_baseline_views.xml',
        'views/app_release_views.xml',
        'views/app_resource_views.xml',
        'views/app_channel_views.xml',
        'views/app_terminal_views.xml',
        'views/app_plugin_views.xml',
        'views/app_menus.xml',
    ],

    'application': True,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}
