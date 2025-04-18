# -*- coding: utf-8 -*-
{
    'name': "Loan Financial",

    'summary': "Financial Management System",

    'description': """
        Financial Management System
    """,

    'author': "HLKJ",
    'website': "https://www.hlgjzn.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations/loan_financial',
    'version': '17.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['loan_basic'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/ir_sequence.xml',
        'data/loan_order_settings.xml',
        'data/payment_channel.xml',
        'views/payment_channel.xml',
        'views/loan_order.xml',
        'views/pay_order.xml',
        'views/repay_order.xml',
        'views/repay_record.xml',
        'views/extension_record.xml',
        'views/additional_record.xml',
        'views/derate_record.xml',
        'views/refund_record.xml',
        'views/settle_record.xml',
        
        'views/platform_flow.xml',
        'views/black_list.xml',
        'views/menu.xml'
    ],
    'application': True,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}

