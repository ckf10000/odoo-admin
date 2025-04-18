# -*- coding: utf-8 -*-
{
    'name': "Loan Settings",
    'summary': "Loan Settings system",
    'description': """
Loan Settings System 
    """,
    'author': "HLKJ",
    'website': "https://www.hlgjzn.com/",
    'category': 'Customizations/loan_settings',
    'version': '17.0.0.1',
    'depends': ['base', 'hr', 'loan_basic'],
    'data': [
        'security/ir.model.access.csv',
        'views/loan_settings_user_views.xml',
        'views/loan_settings_team_views.xml',
        'views/loan_settings_merchant_views.xml',
        'views/loan_settings_role_views.xml',
        'views/menu.xml',
        'data/ir_sequence_data.xml',
        # 'data/loan_settings_role_default_data.xml'
    ],
    'i18n': [
        'i18n/zh_CN.po'
    ],
    'post_load': 'post_load',
    'application': True,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}
