# -*- coding: utf-8 -*-
{
    'name': "Loan Market",

    'summary': "Loan market System ",

    'description': """
        Loan market System 
    """,

    'author': "HLKJ",
    'website': "https://www.hlgjzn.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations/loan_market',
    'version': '17.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['loan_basic'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/app_update_mode.xml',
        'data/app_client_platform.xml',
        'data/app_setting_item.xml',
        'data/ir_sequence_data.xml',
        'data/product_total_amount_type.xml',
        'data/product_quantity_node.xml',
        'data/sms_channel_type.xml',
        'data/sms_template.xml',
        'data/sms_urge_target_type.xml',
        'data/bill_status.xml',
        'views/app.xml',
        'views/app_setting.xml',
        'views/app_version.xml',
        'views/joint_loan_matrix.xml',
        'views/joint_loan.xml',
        'views/product.xml',
        'views/product_quantity.xml',
        'views/combined_set.xml',
        'views/sms_channel_setting.xml',
        'views/sms_app_setting.xml',
        'views/sms_urge_setting.xml',
        'views/menu.xml',
    ],
    'application': True,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}

