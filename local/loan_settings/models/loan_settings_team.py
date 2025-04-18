# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  admin
# FileName:     loan_settings_team.py
# Description:  TODO
# Author:       zw
# CreateDate:   2024/10/30
# Copyright ©2011-2024. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from odoo import models, fields, _, api


class LoanSettingTeam(models.Model):
    _name = 'loan.settings.team'
    _description = 'Team'
    _table = 'R_team'
    _inherit = 'loan.basic.model'
    _rec_name = 'name'
    _order = 'sort asc'

    sequence = fields.Char(string=_('TeamID'), index=True, required=True)
    sort = fields.Integer(string=_('Sorted'))
    hr_depart_id = fields.Many2one('hr.department', string='Department', required=True,
                                   ondelete='cascade', index=True, auto_join=True)
    # name = fields.Char(string=_('Teamname'), related="hr_depart_id.name", store=False)
    name = fields.Char(string=_('Teamname'))
    active = fields.Boolean(string=_('Enable'), default=True)

    # 定义 parent_id 字段，指向同一模型
    # domain：限制选择不包括自身
    parent_id = fields.Many2one('loan.settings.team', string=_('Parent TeamID'), domain="[('id', '!=', id)]",
                                required=False, index=True, auto_join=True)
    merchant_id = fields.Many2one('loan.settings.merchant', string=_('Belong Merchant'), required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)

    formatted_create_date = fields.Char(string=_("Created on"), compute='_compute_formatted_create_date')
    formatted_write_date = fields.Char(string=_("Last Updated on"), compute='_compute_formatted_write_date')

    def create(self, vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('team_code_seq')
        company_id = self.env['loan.settings.merchant'].browse([vals.get("merchant_id")]).company_id.id
        if vals.get("parent_id"):
            parent_id = self.env['loan.settings.team'].browse([vals.get("parent_id")]).hr_depart_id.id
        else:
            parent_id = None
        vals['company_id'] = company_id
        hr_depart = self.env['hr.department'].sudo().create(
            {
                'company_id': company_id,
                'parent_id': parent_id,
                'name': vals.get('name'),
                'complete_name': vals.get('name')
            }
        )
        vals['company_id'] = company_id
        vals['hr_depart_id'] = hr_depart.id
        return super(LoanSettingTeam, self).create(vals)

    def write(self, vals):
        if 'active' in vals and vals['active'] is False:
            self.hr_depart_id.sudo().unlink()
            return super(LoanSettingTeam, self).unlink()
        else:
            update_value = list()
            if "name" in vals:
                update_value.append(f"name = '{vals.get('name')}'")
                update_value.append(f"complete_name = '{vals.get('name')}'")
            if "parent_id" in vals:
                depart_parent_id = self.env['loan.settings.team'].browse([vals.get("parent_id")]).hr_depart_id.id
                if depart_parent_id:
                    update_value.append(f"parent_id = {depart_parent_id}")
                else:
                    update_value.append(f"parent_id = null")
            if "merchant_id" in vals:
                company_id = self.env['loan.settings.merchant'].browse([vals.get("merchant_id")]).company_id.id
                if company_id:
                    update_value.append(f"company_id = {company_id}")
                    vals['company_id'] = company_id
                else:
                    update_value.append(f"company_id = null")
            if update_value:
                update_sql = f"update hr_department set {','.join(update_value)} where id = {self.id}"
                self.env.cr.execute(update_sql)
            # 调用父类的 write 方法，确保数据的正常更新
            return super(LoanSettingTeam, self).write(vals)

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
