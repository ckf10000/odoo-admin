import logging
from odoo import models, fields, api, exceptions, _
from datetime import datetime
from odoo.exceptions import ValidationError


class CollectionPoints(models.Model):
    _name = 'collection.points'
    _table = 'C_points'
    _inherit = ['loan.basic.model']
    _description = '分单管理'
    _sql_constraints = [
        ('user_id_uniq', 'unique(user_id)', _('Single Debt Collector')),
        ('check_max_daily_intake', 'CHECK(max_daily_intake >= 0)',
         _('The Daily Incoming Upper Limit Must Be a Non-negative Integer')),
    ]

    sequence = fields.Char(string=_('Serial Number'),
                           default=lambda self: self.env['ir.sequence'].next_by_code('collection.points'))
    user_id = fields.Many2one('res.users', string=_('Name'))
    group_id = fields.Many2one('res.groups', string=_('Role'))
    collection_stage_id = fields.Many2one('collection.stage.setting', string=_('Collection Phase'))
    collection_stage = fields.Char(string=_('Collection Phase'), related="collection_stage_id.collection_stage",
                                   store=True)
    department_id = fields.Many2one('hr.department', string=_('Membership Group'),
                                    default=lambda self: self.user_id.department_id)
    sec_department_id = fields.Many2one('hr.department', string=_('Subordinate Group'))
    today_processed_qty = fields.Integer(string='Number of Orders Processed Today')  # todo 由待处理订单 跟进后反写
    unprocessed_qty = fields.Integer(string='Number of Unprocessed Orders Remaining',
                                     compute='_compute_unprocessed_qty', store=True)
    max_daily_intake = fields.Integer(string=_('Upper Limit of Daily Incoming'))
    loan_product_ids_str = fields.Char(string=_('Incoming Product Type'), compute='loan_product_ids_str_compute',
                                       store=True)
    loan_product_ids = fields.Many2many('loan.product', string=_('Incoming Product Type'))
    is_input = fields.Boolean(string=_('Either Assign Order or Not'), default=False)
    is_input_select = fields.Selection([('active', _('Open')), ('stop', _('Close'))],
                                       string=_('Either Assign Order or Not'), compute='compute_is_input_select', store=True)
    child_user_ids = fields.Many2many('res.users', string=_('Subordinates'))

    # 用于计算的辅助字段
    today_pending_qty = fields.Integer(string=_('Number of Pending Orders for Today'))  # 由催收员分单记录反写,由定时任务每天晚上清0

    @api.depends('today_pending_qty', 'today_processed_qty')
    def _compute_unprocessed_qty(self):
        for record in self:
            record.unprocessed_qty = record.today_pending_qty - record.today_processed_qty

    @api.onchange('department_id')
    def _onchange_department_id(self):
        self.sec_department_id = False

    @api.depends('loan_product_ids')
    def loan_product_ids_str_compute(self):
        for record in self:
            if len(self.loan_product_ids) == len(self.env['loan.product'].sudo().search([])):
                record.loan_product_ids_str = '全部' if self.env.user.lang == "zh_CN" else "All"
            else:
                record.loan_product_ids_str = ','.join(record.loan_product_ids.mapped('product_name')) if record.loan_product_ids else '-'

    @api.depends('is_input')
    def compute_is_input_select(self):
        for record in self:
            record.is_input_select = 'active' if record.is_input else 'stop'

    def action_server_collection_points(self):
        """
        分单管理action
        """
        context = self.env.context
        tree_view_id = self.env.ref('loan_collection.collection_points_list')
        search_view_id = self.env.ref('loan_collection.collection_points_search')
        action_id = self.env.ref('loan_collection.collection_points_action')
        return {
            'id': action_id.id,
            'type': 'ir.actions.act_window',
            'name': '分单管理' if self.env.user.lang == "zh_CN" else "Order Allocation Management",
            'res_model': self._name,
            'view_mode': 'tree',
            'views': [(tree_view_id.id, 'list')],
            'search_view_id': [search_view_id.id],
            'target': 'current',
            'context': dict(context)
        }

    def action_manager(self):
        """
        列表点击管理按钮
        """
        form_view_id = self.env.ref('loan_collection.collection_points_form')
        return {
            'name': '编辑' if self.env.user.lang == "zh_CN" else "Edit",
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(form_view_id.id, 'form')],
            'target': 'new',
            'context': {'dialog_size': self._action_default_size(), **self._action_default_data()}
        }


    def action_team_adjustment(self):
        """
        列表点击团队调整按钮
        """
        form_view_id = self.env.ref('loan_collection.collection_points_form2')
        return {
            'name': '编辑' if self.env.user.lang == "zh_CN" else "Edit",
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(form_view_id.id, 'form')],
            'target': 'new',
            'context': {'dialog_size': self._action_default_size(), **self._action_default_data()}
        }

    def write(self, vals):
        """编辑保存后增加一条历史记录"""
        result = super(CollectionPoints, self).write(vals)
        if result and self.child_user_ids:
            # 如果更换一级部门导致domain变化，应清除掉非一级部门下的下级用户
            self.child_user_ids = self.child_user_ids.filtered(lambda x: x.department_id in [self.department_id, self.sec_department_id] or x.department_id.parent_id == self.department_id).ids
            # 再更新对应下属的部门
            department_id = self.sec_department_id.id if self.sec_department_id else self.department_id.id
            self.child_user_ids.write({'department_id': department_id, 'parent_id': self.user_id.id})
        return result