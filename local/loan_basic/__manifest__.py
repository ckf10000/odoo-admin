# -*- coding: utf-8 -*-
{
    'name': "Loan Basic",

    'summary': "基础系统",

    'description': """
        基础系统
    """,

    'author': "HLKJ",
    'website': "https://www.hlgjzn.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations/loan_basic',
    'version': '17.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'base_setup', 'web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter.xml',
        'views/res_config_settings.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'loan_basic/static/src/scss/hl_base.scss',
            'loan_basic/static/src/patchs/**/*.js',
            'loan_basic/static/src/patchs/**/*.xml',
            'loan_basic/static/src/client_action/**/*.js',
            'loan_basic/static/src/client_action/**/*.xml',
            'loan_basic/static/src/client_action/**/*.css',
            'loan_basic/static/src/widgets/**/*.js',
            'loan_basic/static/src/widgets/**/*.xml',
            # 'loan_basic/static/src/widgets/button_field/*.js',
            # 'loan_basic/static/src/widgets/button_field/*.xml',
            # 'loan_basic/static/src/widgets/search_date/*.js',
            # 'loan_basic/static/src/widgets/search_date/*.xml',
        ]
    },
    'application': False,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}

