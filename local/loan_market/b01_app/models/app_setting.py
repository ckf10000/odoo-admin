import logging
import json
import ast
from odoo import models, fields, api, exceptions
from ..utils import enums

_logger = logging.getLogger(__name__)


class AppSettingItem(models.Model):
    _name = 'loan.app.setting.item'
    _description = 'App Setting Item'
    _table = 'T_app_setting_item'
    _order = 'sequence'

    item_name = fields.Char(string='配置项名称', required=True)
    enum_code = fields.Integer(string='配置项标识', required=True)
    sub_item_ids = fields.One2many('loan.app.setting.sub.item', 'item_id', string='子配置项')
    sequence = fields.Integer(string='排序', default=0)

    @api.model
    def _get_app_dft_setting_items(self, app_id=None):
        """
        获取app默认设置项
        """
        items = self.search([])
        res = []
        for item in items:
            setting = {
                'app_id': app_id,
                'setting_item_id': item.id
            }
            sub_itmes = item.sub_item_ids.filtered(lambda x: x.sub_item_default_value)
            item_value = {}
            for dx, sub_item in enumerate(sub_itmes):
                # key = dx + 1
                # setting.update({
                #     f"sub_key_{key}": sub_item.sub_item_kind_code,
                #     f'sub_name_{key}': sub_item.sub_item_name,
                #     f'sub_type_{key}': sub_item.sub_item_value_type,
                #     f'sub_val_{key}': sub_item.sub_item_default_value
                # })

                sub_type = sub_item.sub_item_value_type
                value = sub_item.sub_item_default_value
                if sub_type in ('int', 'pct'):
                    value = int(value)
                elif sub_type in ('one2many', 'enum'):
                    value = ast.literal_eval(value)

                item_value.update({
                    sub_item.sub_item_key: {
                        'sub_key': sub_item.sub_item_key,
                        'sub_name': sub_item.sub_item_name,
                        'sub_type': sub_type,
                        'sub_val': value
                    }
                })
            setting.update({
                'item_value': item_value
            })
            res.append(setting)
        return res


class AppSettingSubItem(models.Model):
    _name = 'loan.app.setting.sub.item'
    _description = 'App Setting Sub Item'
    _table = 'T_app_setting_sub_item'

    item_id = fields.Many2one('loan.app.setting.item', string='配置项', required=True)
    sub_item_name = fields.Char(string='配置项名称', required=True)
    sub_item_key = fields.Char(string='子配置项标识', required=True)
    sub_item_value_type = fields.Selection(enums.SUB_ITEM_VALUE_TYPE, string='子配置项值类型', required=True)
    sub_item_default_value = fields.Char(string='子配置项默认值')
    

class AppSetting(models.Model):
    _name = 'loan.app.setting'
    _description = 'App Setting'
    _inherit = ['loan.basic.model']
    _rec_name = 'item_name'
    _table = 'T_app_setting'

    def _get_default_app_id(self):
        app = self.env['loan.app'].search([('status', '=', True)], limit=1)
        return app.id if app else False

    app_id = fields.Many2one(
        'loan.app', 
        string='App名称', 
        required=True, 
        ondelete='cascade',
        auto_join=True,
        default=_get_default_app_id
    )
    matrix_id = fields.Many2one('joint.loan.matrix', string='共贷矩阵', related='app_id.matrix_id')
    active = fields.Boolean(string='启用', related='app_id.active', store=True)
    
    status = fields.Boolean(string='状态', default=True)
    version = fields.Integer(string='版本', default=1)

    setting_item_id = fields.Many2one('loan.app.setting.item', string='关联配置项', required=True, auto_join=True)
    item_name = fields.Char(string='配置项', related='setting_item_id.item_name', store=True)
    item_code = fields.Integer(string='配置键', related='setting_item_id.enum_code', store=True)
    item_overview = fields.Text(string='内容概览', compute='_compute_item_overview', store=True)

    # sub_key_1 = fields.Char(string='子配置键1')
    # sub_name_1 = fields.Char(string='子配置项1')
    # sub_val_1 = fields.Char(string='子配置项1值')
    # sub_type_1 = fields.Char(string='子配置项1类型')

    # sub_key_2 = fields.Char(string='子配置键2')
    # sub_name_2 = fields.Char(string='子配置项2')
    # sub_val_2 = fields.Char(string='子配置项2值')
    # sub_type_2 = fields.Char(string='子配置项2类型')

    # sub_key_3 = fields.Char(string='子配置键3')
    # sub_name_3 = fields.Char(string='子配置项3')
    # sub_val_3 = fields.Char(string='子配置项3值')
    # sub_type_3 = fields.Char(string='子配置项3类型')

    item_value = fields.Json(string='配置项值')

    @api.depends('item_value')
    def _compute_item_overview(self):
        for rec in self:
            rec.item_overview = ''
            if not rec.item_value:
                rec.item_overview = ''
                continue

            msg = []
            need_name = False if len(rec.item_value) < 2 else True
            for sub in rec.item_value.values():
                val = sub.get('sub_val', '')
                if not val:
                    continue

                sub_type = sub.get('sub_type')
                if sub_type == "one2many":
                    continue

                if sub_type == 'pct':
                    val = f"{val}%"
                elif sub_type in ['enum', 'many2one']:
                    val = val[1]
                elif sub_type == 'int':
                    val = str(val)
                
                if need_name:
                    msg.append(f"{sub.get('sub_name')}: {val}")
                else:
                    msg.append(val)
            rec.item_overview = "/".join(msg)

    def _get_action_data(self, extra_data=None):
        """
        解析子配置项值,用于修改
        """
        context_data = {'default_setting_id': self.id, 'dialog_size': 'medium'}
        if extra_data:
            context_data.update(extra_data)
        if not self.item_value:
            return context_data
        
        for sub in self.item_value.values():
            value = sub.get('sub_val')
            if not value:
                continue
            key = f"default_{sub.get('sub_key')}"
            sub_type = sub.get('sub_type')
            if sub_type == 'pct':
                value = value/100
            elif sub_type == 'int':
                value = int(value)
            elif sub_type in ['enum', 'many2one']:
                value = value[0]
            elif sub_type == 'one2many':
                value = [(6, 0, [i[0] for i in value])]
            context_data[key] = value
        return context_data

    def action_update_item(self):
        context_data = self._get_action_data()
        return {
            'name': f'编辑{self.item_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'loan.app.setting.edit.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': context_data
        }

    def action_view_item(self, target="new"):
        """
        不同配置项的预览方式不一样，需要根据配置项类型进行判断
        """
        if self.item_code in (5, 6, 7, 9):
            value = ""
            if self.item_value:
                value = "".join([i.get('sub_val') for i in self.item_value.values()])
            context_data = {
                'content': value,
                'dialog_size': 'small'
            }
            return {
                "name": f"查看{self.item_name}",
                "type": "ir.actions.client",
                "tag": "mobile_view_client_action",
                "target": target,
                "context": context_data
            }
        
        context_data = self._get_action_data({'readonly': True})
        return {
            'name': f'查看{self.item_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'loan.app.setting.edit.wizard',
            'view_mode': 'form',
            'target': target,
            'context': context_data
        }


class AppAuthMode(models.Model):
    _name = 'loan.app.setting.auth.mode'
    _description = 'App Setting Auth Mode'
    _order = 'sequence'
    _rec_name = 'mode_name'
    _table = 'T_app_auth_mode'

    enum_code = fields.Integer(string='枚举编码', required=True)
    mode_name = fields.Char(string='模式名称', required=True)
    sequence = fields.Integer(string='排序', required=True)


class AppSettingEditWizard(models.TransientModel):
    _name = 'loan.app.setting.edit.wizard'
    _description = 'App Setting Edit Wizard'
    _inherit = ['loan.basic.model']

    setting_id = fields.Many2one('loan.app.setting', string='配置项', required=True)
    setting_item_id = fields.Many2one('loan.app.setting.item', string='配置项', related="setting_id.setting_item_id")
    app_id = fields.Many2one('loan.app', string='App', related='setting_id.app_id')
    matrix_id = fields.Many2one('joint.loan.matrix', string='共贷矩阵', related='setting_id.matrix_id')
    item_kind_code = fields.Integer(string='配置键', related='setting_id.item_code')

    compare_pass_rate = fields.Float(string='对比通过率')
    daily_call_count = fields.Integer(string='每日调用次数')
    register_call_count = fields.Integer(string='填资环节每日允许调用次数')

    af_key = fields.Char(string='AppsFlyer dev key')

    loan_protocol = fields.Html(string='借款协议')
    privacy_protocol = fields.Html(string='隐私协议')
    auth_content = fields.Html(string='授权文案')
    about_us = fields.Html(string='关于我们')

    cs_tel = fields.Char(string='客服电话')
    cs_email = fields.Char(string='客服邮箱')
    cs_work_time = fields.Char(string='客服时间')

    new_product_count = fields.Integer(string='新客产品展示数量')
    product_pool_ids = fields.Many2many('loan.product', 'app_setting_product_pool_rel', 'sid', 'pid', string='新客产品池', domain="[('matrix_id', '=', matrix_id)]")

    data_auth_type = fields.Many2one('loan.app.setting.auth.mode', string='数据授权获取方式')

    @api.model
    def _check_data(self, data):
        """
        检查数据, 并一次性抛出所有错误
        """
        errors = []

        if 'compare_pass_rate' in data and not (0.0 <= data['compare_pass_rate'] <= 1.0):
            errors.append(f'对比通过率: 请输入数值(0-100)')
        
        if 'daily_call_count' in data and data['daily_call_count'] < 0:
            errors.append(f'每日调用次数: 请输入≥0的整数')

        if 'register_call_count' in data and data['register_call_count'] < 0:
            errors.append(f'填资环节允许调用次数: 请输入≥0的整数')


        if errors:
            raise exceptions.ValidationError(self.format_action_error(errors))

    def save_setting(self):
        """
        保存设置
        """
        item_value = {}
        for sub_item in self.setting_item_id.sub_item_ids:
            sub_key = sub_item.sub_item_key
            sub_name = sub_item.sub_item_name
            sub_type = sub_item.sub_item_value_type
            sub_val = getattr(self, sub_key)
            if sub_type == 'pct':
                sub_val = int(sub_val*100) if sub_val else 0
            elif sub_type == 'many2one':
                sub_val = [sub_val.id, sub_val.display_name] if sub_val else None
            elif sub_type == 'one2many':
                sub_val = [(p.id, p.display_name) for p in sub_val]
            
            item_value.update({
                sub_key: {
                    'sub_key': sub_key,
                    'sub_name': sub_name,
                    'sub_val': sub_val,
                    'sub_type': sub_type
                }
            })
        
        if item_value:
            self.setting_id.write({"item_value": item_value})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_data(vals)
        res = super().create(vals_list)

        for obj in res:
            obj.save_setting()
        return res
    
    # def action_view_item(self):
    #     return self.setting_id.action_view_item()
