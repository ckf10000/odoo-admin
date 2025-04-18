# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  admin
# FileName:     loan_settings_merchant.py
# Description:  TODO
# Author:       zw
# CreateDate:   2024/10/30
# Copyright ©2011-2024. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from odoo import models, fields, _, api
from ..libs.converter import ModelKwargsConverter


class LoanSettingMerchant(models.Model):
    _name = 'loan.settings.merchant'
    _description = 'Merchant'
    _table = 'R_merchant'
    _inherit = 'loan.basic.model'
    _rec_name = 'name'

    sequence = fields.Char(string=_('MerchantID'), index=True, required=True)
    res_partner_id = fields.Many2one("res.partner", string="Partner", required=True, index=True, auto_join=True)
    phone = fields.Char(string=_('Contact Information'), related="res_partner_id.phone", store=False, required=True)
    company_id = fields.Many2one('res.company', string='Merchant', required=True, index=True, auto_join=True)
    name = fields.Char(string=_('Merchant Name'), related="company_id.name", store=False)
    contact_user = fields.Char(string=_("Contact Person"), required=True)
    active = fields.Boolean(string=_('Enable'), default=True)

    formatted_create_date = fields.Char(string=_("Created on"), compute='_compute_formatted_create_date')
    formatted_write_date = fields.Char(string=_("Last Updated on"), compute='_compute_formatted_write_date')

    def create(self, vals):
        partner = self.env['res.partner'].sudo().create(
            {
                'name': vals.get('name'),
                'phone': vals.get('phone'),
                'is_company': True,
                'lang': self.env.context.get('lang'),
                'tz': self.env.user.tz,
                'complete_name': vals.get('name'),
                'active': vals.get('active')
            }
        )
        res_company = self.env['res.company'].sudo().create(
            {
                'name': vals.get('name'),
                'partner_id': partner.id,
                'currency_id': 20,  # 货币id， 印度卢比 INR,
                'phone': vals.get('phone'),
                'layout_background': 'Blank'
            }

        )
        vals['sequence'] = self.env['ir.sequence'].next_by_code('merchant_code_seq')
        vals['res_partner_id'] = partner.id
        vals['company_id'] = res_company.id
        return super(LoanSettingMerchant, self).create(vals)

    def write(self, vals):
        if 'active' in vals and vals['active'] is False:
            self.res_partner_id.sudo().write({'active': False})
            self.company_id.sudo().write({'active': False})
            return super(LoanSettingMerchant, self).write({'active': False})
        else:
            res_partner_kw = ModelKwargsConverter.get_res_partner_kwargs(vals=vals)
            res_company_kw = ModelKwargsConverter.get_res_company_kwargs(vals=vals)
            self.env['res.partner'].browse(self.res_partner_id.id).write(res_partner_kw)
            self.env['res.company'].browse(self.company_id.id).write(res_company_kw)
            # 调用父类的 write 方法，确保数据的正常更新
            return super(LoanSettingMerchant, self).write(vals)

    @api.depends('create_date')
    def _compute_formatted_create_date(self):
        # 将时间转换为用户时区
        user_tz = self.env.user.tz or 'UTC'
        for record in self:
            create_date = fields.Datetime.context_timestamp(self, record.create_date)
            record.formatted_create_date = create_date.strftime('%Y-%m-%d %H:%M:%S') if create_date else ''

    @api.depends('write_date')
    def _compute_formatted_write_date(self):
        # 将时间转换为用户时区
        user_tz = self.env.user.tz or 'UTC'
        for record in self:
            write_date = fields.Datetime.context_timestamp(self, record.write_date)
            record.formatted_write_date = write_date.strftime('%Y-%m-%d %H:%M:%S') if write_date else ''
