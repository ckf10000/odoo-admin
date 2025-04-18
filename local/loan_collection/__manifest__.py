# -*- coding: utf-8 -*-
{
    'name': "Loan Collection",

    'summary': "Loan collection system",

    'description': """
        Loan collection system
    """,

    'author': "HLKJ",
    'website': "https://www.hlgjzn.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations/loan_collection',
    'version': '17.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['loan_basic', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 催收分单管理
        'data/ir_cron.xml',
        'data/ir_sequence.xml',
        'data/res_groups.xml',
        'data/collection_auto_assign_orders.xml',
        'views/collection_stage_setting_views.xml',
        'views/collection_stage_setting_history_views.xml',
        'views/collection_points_views.xml',
        'wizard/collection_stage_setting_wizard.xml',
        # 催收订单管理
        'views/collection_order.xml',
        'views/collection_order_allot_views.xml',
        'views/collection_order_pending_views.xml',
        'views/collection_order_process_views.xml',
        'views/collection_user_contact_views.xml',
        # 'views/collection_reduction_examine_record_views.xml',
        # 'views/collection_auto_examine_views.xml',
        # 'views/blacklist_management_views.xml',
        # 'views/replenishment_record_views.xml',
        'wizard/manual_allocation_wizard.xml',
        'wizard/reduction_examine_wizard.xml',
        # 金额减免管理
        'views/derate_record.xml',
        'views/additional_record.xml',
        'views/extension_record.xml',
        'views/loan_order_line.xml',
        'views/finance_balance_accounts.xml',
        #菜单
        'views/menu.xml',
    ],
    'i18n': [
        'i18n/zh_CN.po'
    ],
    'application': True,
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}

