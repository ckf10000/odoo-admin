# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  admin
# FileName:     loan_settings_user.py
# Description:  TODO
# Author:       zw
# CreateDate:   2024/10/30
# Copyright ©2011-2024. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import re
from odoo import models, fields, _, api, exceptions
from ..libs.converter import ModelKwargsConverter


class LoanSettingUsers(models.Model):
    _name = 'loan.settings.user'
    _description = 'User'
    _table = 'R_user'
    _inherit = 'loan.basic.model'
    # _rec_name = 'name'
    _order = 'write_date desc'

    sequence = fields.Char(string=_('UserID'), index=True, required=True)
    # is_collection = fields.Boolean(string=_('Is it a collector'), default=False)
    res_user_id = fields.Many2one("res.users", string="User", required=True, index=True, auto_join=True)
    # res_partner_id = fields.Many2one("res.partner", string="Partner", required=True, index=True, auto_join=True)
    login = fields.Char(string=_('Login'), related="res_user_id.login", store=False)
    password = fields.Char(string=_("Password"), related="res_user_id.password", store=False)
    # name = fields.Char(string=_('Username'), related='res_partner_id.name', store=False)
    # phone = fields.Char(string=_('Phone'), related='res_partner_id.phone', store=False)
    # lang = fields.Selection(string=_('Language'), related='res_partner_id.lang', store=False)
    # tz = fields.Selection(string=_('Timezone'), related='res_partner_id.tz', store=False)
    merchant_id = fields.Many2one('loan.settings.merchant', string=_('Belong Merchant'), required=True, auto_join=True)
    res_company_id = fields.Many2one('res.company', string='Company', required=True, auto_join=True)
    team_id = fields.Many2one('loan.settings.team', string=_('Belong Team'), required=True, auto_join=True, domain="[('merchant_id', '=', merchant_id)]")
    # hr_depart_id = fields.Many2one('hr.department', string='Department', required=True, auto_join=True)
    role_ids = fields.Many2many(
        'loan.settings.role',
        'R_role_user_rel',
        'uid',
        'rid',
        ondelete='restrict',
        string=_('Role')
    )
    # 新增的 Many2many 字段，用于关联下属用户
    subordinates_ids = fields.Many2many(
        'loan.settings.user',
        'R_user_subordinates_rel'
        'uid',
        'did',
        string=_('Subordinates')
    )

    active = fields.Boolean(string=_('Enable'), default=True)
    formatted_create_date = fields.Char(string=_("Created on"), compute='_compute_formatted_create_date')
    formatted_write_date = fields.Char(string=_("Last Updated on"), compute='_compute_formatted_write_date')

    @api.constrains('res_user_id')
    def _check_login(self):
        for record in self:
            # 通过 res_user_id 访问 login 字段
            if record.res_user_id.login and not bool(re.match(
                    "^[^\u4e00-\u9fa5\u0800-\u4e00\u0600-\u06FF\u0300-\u036F]+$", record.res_user_id.login)):
                msg = "用户名只有由字母、数字或字符组成！" if self.env.user.lang == "zh_CN" else \
                    "The Login must consist of only letters, numbers, or symbols!"
                raise exceptions.ValidationError(msg)
            
    @api.onchange('merchant_id')
    def _onchange_merchant_id(self):
        """
        切换商户时,团队置为空
        """
        self.team_id = False

    def create(self, vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('user_code_seq')
        res_company_id = self.env['loan.settings.merchant'].browse([vals.get("merchant_id")]).company_id.id
        hr_depart_id = self.env['loan.settings.team'].browse([vals.get("team_id")]).hr_depart_id.id
        partner_kwargs = ModelKwargsConverter.get_res_partner_kwargs(vals=vals)
        partner_kwargs.update(dict(company_id=res_company_id))
        partner = self.env['res.partner'].sudo().create(partner_kwargs)
        if vals.get('role_ids'):
            add_group_ids, _ = ModelKwargsConverter.parse_many2many_args(*vals.get('role_ids'))
        else:
            add_group_ids = list()
        if vals.get('subordinates_ids'):
            add_subordinates_ids, _ = ModelKwargsConverter.parse_many2many_args(*vals.get('subordinates_ids'))
            loan_settings_user = self.env['loan.settings.user'].browse(add_subordinates_ids)
            sub_user_ids = [x.res_user_id.id for x in loan_settings_user]
        else:
            sub_user_ids = list()
        role_ids = self.env['loan.settings.role'].sudo().browse(add_group_ids)
        raw_role_ids = [role_id.res_groups_id.id for role_id in role_ids]

        res_users = self.env['res.users'].sudo().create(
            {
                'company_id': res_company_id,
                'department_id': hr_depart_id,
                'partner_id': partner.id,
                'login': vals.get('login'),
                'dialog_size': 'minimize',
                'notification_type': 'email',
                'sidebar_type': 'large',
                'chatter_position': 'side',
                'company_ids': [(4, res_company_id)]
            }
        )
        self.env['res.groups'].browse(raw_role_ids).write(
            {
                "users": [(4, res_users.id)]
            }
        )
        vals['is_collection'] = res_users.has_group('loan_collection.loan_collector_group')
        if vals['is_collection']:
            self.env['collection.points'].sudo().create({
                'sequence': self.env['ir.sequence'].next_by_code('collection.points'),
                'user_id': res_users.id,
                'group_id': self.env.ref('loan_collection.loan_collector_group').id,
                'collection_stage_id': False,
                'department_id': res_users.department_id.id,
                'is_input': False,
                'loan_product_ids': self.env['loan.product'].sudo().search([]).ids,
                'is_input_select': 'stop',
                'active': True
            })
        res_users.sudo().write({'is_collection': vals['is_collection']})
        user_id = res_users.id
        if sub_user_ids:
            self.env['res.users'].browse(sub_user_ids).sudo().write({
                "parent_id": user_id
            })
        self.env['res.users'].browse(res_users.id)._change_password(vals.get('password'))
        admin_ids = list()
        self.env.cr.execute("select * from res_groups")
        # 获取查询结果
        res_groups_ids = self.env.cr.fetchall()
        for res_groups_id in res_groups_ids:
            if res_groups_id[1].get("en_US") == "Administrator":
                admin_ids.append(str(res_groups_id[0]))
        if admin_ids:
            del_sql = f"delete from res_groups_users_rel where uid={res_users.id} and gid in ({','.join(admin_ids)})"
            self.env.cr.execute(del_sql)
        vals['res_user_id'] = res_users.id
        vals['hr_depart_id'] = hr_depart_id
        vals['res_partner_id'] = partner.id
        vals['company_id'] = vals['res_company_id'] = res_company_id
        res = super(LoanSettingUsers, self).create(vals)
        self.env.cr.commit()
        res_users = self.env['res.users'].search([('id', '=', user_id)], limit=1)
        if res_users:
            # 更新 collection.points 记录
            if res_users.has_group('loan_collection.loan_collector_group'):
                is_collection = 't'
                collection_sql = f'update "C_points" set department_id={hr_depart_id},active=\'t\' where user_id={user_id}'
                self.env.cr.execute(collection_sql)
            else:
                is_collection = 'f'
            users_sql = f'update "res_users" set is_collection=\'{is_collection}\' where id={user_id}'
            self.env.cr.execute(users_sql)
        return res

    def write(self, vals):
        if 'active' in vals and vals['active'] is False:
            self.env.cr.execute(
                "update res_partner set active='f' where id=%s", (self.res_partner_id.id,)
            )
            self.env.cr.execute(
                "update res_users set active='f' where id=%s", (self.res_user_id.id,)
            )
            self.env.cr.execute(
                'update "C_points" set active=\'f\' where id=%s', (self.res_user_id.id,)
            )
            return super(LoanSettingUsers, self).write({'active': False})
        elif 'active' in vals and vals['active'] is True:
            self.env.cr.execute(
                "update res_partner set active='t' where id=%s", (self.res_partner_id.id,)
            )
            self.env.cr.execute(
                "update res_users set active='t' where id=%s", (self.res_user_id.id,)
            )
            self.env.cr.execute(
                'update "C_points" set active=\'t\' where id=%s', (self.res_user_id.id,)
            )
            return super(LoanSettingUsers, self).write({'active': True})
        else:
            points_update = list()
            users_update = list()
            user_id = self.res_user_id.id
            if vals.get('subordinates_ids'):
                add_subordinates_ids, del_subordinates_ids = ModelKwargsConverter.parse_many2many_args(
                    *vals.get('subordinates_ids')
                )
                if add_subordinates_ids:
                    loan_settings_user_1 = self.env['loan.settings.user'].browse(add_subordinates_ids)
                    add_sub_user_ids = [x.res_user_id.id for x in loan_settings_user_1]
                else:
                    add_sub_user_ids = list()
                if del_subordinates_ids:
                    loan_settings_user_2 = self.env['loan.settings.user'].browse(del_subordinates_ids)
                    del_sub_user_ids = [x.res_user_id.id for x in loan_settings_user_2]
                else:
                    del_sub_user_ids = list()
            else:
                add_sub_user_ids = del_sub_user_ids = list()
            if "merchant_id" in vals:
                res_company_id = self.env['loan.settings.merchant'].browse([vals.get("merchant_id")]).company_id.id
                vals['company_id'] = vals['res_company_id'] = res_company_id
                self.env.cr.execute(
                    'delete from res_company_users_rel where cid=%s and user_id=%s',
                    (self.res_user_id.company_id.id, self.res_user_id.id)
                )
                self.env['res.users'].browse(self.res_user_id.id).write(
                    {
                        'company_id': res_company_id,
                        'company_ids': [(4, res_company_id)]
                    }
                )
                points_update.append(f"company_id={res_company_id}")
                users_update.append(f"company_id={res_company_id}")
            if "team_id" in vals:
                vals['hr_depart_id'] = hr_depart_id = self.env['loan.settings.team'].browse(
                    [vals.get("team_id")]).hr_depart_id.id
                points_update.append(f"department_id={hr_depart_id}")
            if vals.get('name'):
                vals['complete_name'] = vals.get('name')
            role_ids = vals.get('role_ids', list()) or list()
            partner_kwargs = ModelKwargsConverter.get_res_partner_kwargs(vals=vals)
            if partner_kwargs:
                self.env['res.partner'].browse(self.res_partner_id.id).write(partner_kwargs)
            add_group_ids, del_group_ids = ModelKwargsConverter.parse_many2many_args(*role_ids)
            if add_group_ids:
                add_role_ids = self.env['loan.settings.role'].sudo().browse(add_group_ids)
                raw_role_ids = [role_id.res_groups_id.id for role_id in add_role_ids]
                self.env['res.groups'].browse(raw_role_ids).write(
                    {
                        "users": [(4, self.res_user_id.id)]
                    }
                )
            if del_group_ids:
                del_role_ids = self.env['loan.settings.role'].sudo().browse(del_group_ids)
                raw_role_ids = [role_id.res_groups_id.id for role_id in del_role_ids]
                self.env['res.groups'].browse(raw_role_ids).write(
                    {
                        "users": [(3, self.res_user_id.id)]
                    }
                )
            if add_sub_user_ids:
                self.env['res.users'].browse(add_sub_user_ids).sudo().write({
                    "parent_id": user_id
                })
            if del_sub_user_ids:
                self.env['res.users'].browse(del_sub_user_ids).sudo().write({
                    "parent_id": None
                })
            vals.pop("complete_name", None)
            res = super(LoanSettingUsers, self).write(vals)
            self.env.cr.commit()
            res_users = self.env['res.users'].search([('id', '=', user_id)], limit=1)
            is_exist = self.env["collection.points"].search([('user_id', '=', user_id),('active', 'in', [True, False])], limit=1)
            if res_users.has_group('loan_collection.loan_collector_group'):
                if len(is_exist) > 0:
                    points_update.append(f"active='t'")
                else:
                    self.env['collection.points'].sudo().create({
                        'sequence': self.env['ir.sequence'].next_by_code('collection.points'),
                        'user_id': self.res_user_id.id,
                        'group_id': self.env.ref('loan_collection.loan_collector_group').id,
                        'collection_stage_id': False,
                        'department_id': self.res_user_id.department_id.id,
                        'is_input': False,
                        'loan_product_ids': self.env['loan.product'].sudo().search([]).ids,
                        'is_input_select': 'stop',
                        'active': True
                    })
                users_update.append(f"is_collection='t'")
            else:
                if len(is_exist) > 0:
                    points_update.append(f"active='f'")
                users_update.append(f"is_collection='f'")
            if users_update:
                sql = f"update res_users set {','.join(users_update)} where id={user_id}"
                self.env.cr.execute(sql)
            if points_update:
                con = ','.join(points_update)
                sql = f'update "C_points" set {con} where user_id={user_id}'
                self.env.cr.execute(sql)
            return res

    def unlink(self):
        ids_str = ','.join([str(x) for x in self.res_user_id.ids])
        partner_ids_str = ','.join([str(x) for x in self.res_user_id.partner_id.ids])
        # 删除对应用户分单管理
        del_sql = f'delete from "C_points" where user_id in ({ids_str})'
        self.env.cr.execute(del_sql)
        del_sql = f'delete from res_partner where id in ({partner_ids_str})'
        self.env.cr.execute(del_sql)
        del_sql = f'delete from res_users where id in ({ids_str})'
        self.env.cr.execute(del_sql)
        # self.env['collection.points'].sudo().search([('user_id', 'in', self.res_user_id.ids)]).unlink()
        # self.env['res.partner'].sudo().browse(self.res_user_id.partner_id.id).unlink()
        # self.env['res.users'].sudo().browse(self.res_user_id.ids).unlink()
        # 删除对应的用户数据
        return super(LoanSettingUsers, self).unlink()

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
