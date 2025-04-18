# -*- coding: utf-8 -*-
{
    'name': "Loan Theme",

    'summary': "Loan theme",

    'description': """
        Loan theme
    """,

    'author': "HLKJ",
    'website': "https://www.hlgjzn.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations/loan_theme',
    'version': '17.0.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base_setup',
        'web_editor'
    ],

    # always loaded
    'data': [
        'templates/webclient.xml',
        'views/res_config_settings.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'loan_theme/static/src/scss/colors.scss'),
            (
                'before', 
                'loan_theme/static/src/scss/colors.scss', 
                'loan_theme/static/src/scss/colors_light.scss'
            ),
        ],
        'web.assets_web_dark': [
            (
                'after', 
                'loan_theme/static/src/scss/colors.scss', 
                'loan_theme/static/src/scss/colors_dark.scss'
            ),
        ],
    },
    'images': [
        # 'static/description/banner.png',
    ],
    'application': True,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}

