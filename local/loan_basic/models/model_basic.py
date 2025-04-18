# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


# def convert_to_record(self, value, record):
#         return value or 0

# fields.Integer.convert_to_record = convert_to_record


class LoanBasicModel(models.AbstractModel):
    _name = 'loan.basic.model'
    _description = '基础模型'

    company_id = fields.Many2one('res.company', string='公司', default=lambda self: self.env.company)
    active = fields.Boolean(string='启用', default=True)

    @api.model
    def _action_default_size(self):
        return 'medium'
    
    @api.model
    def _action_default_data(self):
        return {}
    
    def action_edit(self):
        """
        列表点击编辑按钮
        """
        return {
            'name': '编辑' if self.env.user.lang == "zh_CN" else "Edit",
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'dialog_size': self._action_default_size(), **self._action_default_data()}
        }
    
    def action_create(self):
        """
        列表点击新增按钮
        """
        return {
            'name': '新增' if self.env.user.lang == "zh_CN" else "Add",
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'target': 'new',
            'context': {'dialog_size': self._action_default_size(), **self._action_default_data()}
        }

    @api.model
    def format_action_error(self, errors):
        """
        列表点击错误按钮
        """
        return ("\n").join([f"{dx+1}. {err}" for dx, err in enumerate(errors)])
 
    @api.model
    def _check_data(self, data):
        """
        检查数据, 并一次性抛出所有错误
        """
        errors = []
        if errors:
            raise exceptions.ValidationError(self.format_action_error(errors))

    @api.model
    def create(self, vals):
        self._check_data(vals)
        return super().create(vals)
    
    def write(self, val):
        check_info = {field: getattr(self, field, None) for field in self._fields}
        check_info.update(val)
        self._check_data(check_info)
        return super().write(val)