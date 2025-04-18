# -*- coding: utf-8 -*-
{
    'name': "Loan CSS",

    'summary': "Customer Service System",

    'description': """
        Customer Service System
    """,

    'author': "HLKJ",
    'website': "https://www.hlgjzn.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations/loan_css',
    'version': '17.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['loan_basic'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
    ],
    'application': False,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}

