# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, exceptions
from odoo.osv import expression
import datetime
from dateutil import relativedelta

# def convert_to_record(self, value, record):
#         return value or 0

# fields.Integer.convert_to_record = convert_to_record


class LoanBasicModel(models.AbstractModel):
    _name = 'loan.basic.model'
    _description = '基础模型'

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
        for obj in self:
            check_info = {field: getattr(obj, field, None) for field in obj._fields}
            check_info.update(val)
            self._check_data(check_info)
        return super().write(val)
    
    @api.model
    def _format_date_search_domain(self, field, val, unit):
        now = datetime.datetime.utcnow()
        if unit == 'second':
            dt = now - relativedelta.relativedelta(seconds=val)
        elif unit == 'minute':
            dt = now - relativedelta.relativedelta(minutes=val)
        elif unit == 'hour':
            dt = now - relativedelta.relativedelta(hours=val)
        elif unit == 'day':
            dt = now - relativedelta.relativedelta(days=val)
        elif unit == 'week':
            dt = now - relativedelta.relativedelta(weeks=val)
        elif unit == 'month':
            dt = now - relativedelta.relativedelta(months=val)
        else:
            dt = now - relativedelta.relativedelta(years=val)
        return [(field, '>=', dt.strftime('%Y-%m-%d 00:00:00'))]

    @api.model
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        context = self.env.context
        default_domain = context.get('default_search_domain', [])

        search_flag = context.get('search_flag', False)
        if search_flag and not domain:
            return {"length": 0, "records": []}
        
        if domain == default_domain:
            for field, val, unit in self.env.context.get('date_search_domain', []):
                if not domain or not len(list(filter(lambda x: x[0] == field, domain))):
                    domain = expression.AND([domain, self._format_date_search_domain(field, val, unit)])
        
        res = super().web_search_read(domain, specification, offset, limit, order, count_limit)
        return res


class CompanyFieldMixin(models.AbstractModel):
    _name = 'company.field.mixin'

    company_id = fields.Many2one('res.company', string='商户', default=lambda self: self.env.company, index=True)

    
class AppVersionFieldMixin(models.AbstractModel):
    _name = 'app.version.field.mixin'

    app_version = fields.Char(string='App Version')
    app_version_code = fields.Integer(string='App Version Code')