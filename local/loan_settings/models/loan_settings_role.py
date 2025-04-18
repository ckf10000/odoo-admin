# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  admin
# FileName:     loan_settings_role.py
# Description:  TODO
# Author:       zw
# CreateDate:   2024/10/31
# Copyright ©2011-2024. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from odoo import models, fields, _, api
from ..libs.repository import ModelRepository
from ..libs.converter import ModelKwargsConverter


class LoanSettingsRole(models.Model):
    _name = 'loan.settings.role'
    _description = 'Role'
    _table = 'R_role'
    _inherit = 'loan.basic.model'
    _rec_name = 'name'

    sequence = fields.Char(string=_('RoleID'), index=True, required=True)
    res_groups_id = fields.Many2one('res.groups', string='Groups', required=True,
                                    index=True, ondelete='cascade', auto_join=True)
    name = fields.Char(string=_('Role Name'), required=True)
    access_limit = fields.Selection([('1', _('不限')), ('2', _('自定义'))], string=_('Allow Access Date'),
                                    required=True, default='1')
    start_date = fields.Date(string=_('Start Date'))
    end_date = fields.Date(string=_('End Date'))
    active = fields.Boolean(string=_('Enable'), default=True)

    formatted_create_date = fields.Char(string=_("Created on"), compute='_compute_formatted_create_date')
    formatted_write_date = fields.Char(string=_("Last Updated on"), compute='_compute_formatted_write_date')

    menu_ids = fields.Many2many(
        'ir.ui.menu',
        'R_role_menu_rel',
        'rid',
        'mid',
        ondelete='cascade',
        string=_('Menu')
    )

    def create(self, vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('role_code_seq')
        res_groups = self.env['res.groups'].sudo().create(
            {
                'name': vals.get('name')
            }
        )
        vals['res_groups_id'] = res_groups.id
        _menu_ids = vals.get("menu_ids")
        if _menu_ids:
            add_menu_ids, _ = ModelKwargsConverter.parse_many2many_args(*_menu_ids)
            # 要添加的 角色 与 菜单 的关系
            rel = [(4, res_groups.id)]
            admin_ids = ModelRepository.get_administrator_ids(model=self)
            if admin_ids:
                # 默认插入 管理员 与 菜单的关联关系
                for admin_id in admin_ids:
                    rel.append((4, admin_id))
            # 批量向菜单关联角色
            self.env['ir.ui.menu'].browse(add_menu_ids).write({
                'groups_id': rel
            })
        return super(LoanSettingsRole, self).create(vals)

    def write(self, vals):
        if 'active' in vals and vals['active'] is False:
            self.res_groups_id.sudo().unlink()
            return super(LoanSettingsRole, self).unlink()
        else:
            _menu_ids = vals.get('menu_ids')
            if _menu_ids:
                add_menu_ids, del_menu_ids = ModelKwargsConverter.parse_many2many_args(*_menu_ids)
                if add_menu_ids:
                    rel = [(4, self.res_groups_id.id)]
                    admin_ids = ModelRepository.get_administrator_ids(model=self)
                    if admin_ids:
                        # 默认插入 管理员 与 菜单的关联关系
                        for admin_id in admin_ids:
                            rel.append((4, admin_id))
                    # 批量添加关系
                    self.env['ir.ui.menu'].browse(add_menu_ids).write({'groups_id': rel})
                if del_menu_ids:
                    # 批量添加关系
                    self.env['ir.ui.menu'].browse(del_menu_ids).write({
                        'groups_id': [
                            (3, self.res_groups_id.id)  # 删除角色 ID
                        ]
                    })
            # 调用父类的 write 方法，确保数据的正常更新
            return super(LoanSettingsRole, self).write(vals)

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
