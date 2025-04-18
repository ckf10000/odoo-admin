from odoo import models, fields, api, exceptions
from datetime import datetime, date


class ResUsers(models.Model):
    _inherit = 'res.users'

    department_id = fields.Many2one('hr.department', string='部门')
    is_collection = fields.Boolean(string='是否为催收员', default=False)
    parent_id = fields.Many2one('res.users', string='上级')

    @api.model  
    def write(self, values):  
        # 调用父类的 write 方法，确保其返回结果  
        result = super(ResUsers, self).write(values)  

        for record in self:
            # 检查用户是否是催收员，并确保在正确的上下文中使用
            if record.has_group('loan_collection.loan_collector_group'):
                is_collection_collector = True

                # 使用 sudo 来确保我们具备足够的权限去访问其他模型
                points_ids = record.env['collection.points'].sudo().search([('user_id', '=', record.id)])

                # 更新分单管理的活动状态
                for points_id in points_ids:
                    points_id.active = is_collection_collector

        return result  

    @api.model
    def create(self, values):
        res_id = super(ResUsers, self).create(values)
        self.env['collection.points'].sudo().create({
            'sequence': self.env['ir.sequence'].next_by_code('collection.points'),
            'user_id': res_id.id,
            'group_id': self.env.ref('loan_collection.loan_collector_group').id,
            'collection_stage_id': False,
            'department_id': res_id.department_id.id,
            'is_input': False,
            'loan_product_ids': self.env['loan.product'].sudo().search([]).ids,
            'is_input_select': 'stop',
            'active': res_id.has_group('loan_collection.loan_collector_group')
        })
        res_id.sudo().write({'is_collection': res_id.has_group('loan_collection.loan_collector_group')})
        return res_id

    def unlink(self):
        # 删除对应用户分单管理
        self.env['collection.points'].sudo().search([('user_id', 'in', self.ids)]).unlink()
        return super(ResUsers, self).unlink()

    @api.model
    def _search(self, args, offset=0, limit=None, order=None,  access_rights_uid=None):
        args = args or []
        domain = []
        
        if 'bill_search' in self.env.context:
            if self.env.context['bill_search'] == 'manual.allocation.wizard':
                if "collection_stage" not in self.env.context:
                    cache_data = {str(key): value for key, value in dict(self.env.cache._data).items()}
                    collection_stage_dict = cache_data.get("manual.allocation.wizard.collection_stage")
                    if collection_stage_dict and isinstance(collection_stage_dict, dict):
                        temp_context = dict(collection_stage=next(iter(collection_stage_dict.values())))
                        temp_context.update(self.env.context)
                        self.env.context = temp_context
                    else:
                        return
                
                # 先找出 催收员“是否进件”状态为“开启”、“催收阶段”与所选择订单的“催收阶段”一致的记录
                points_ids = self.env['collection.points'].sudo().search([('is_input', '=', True), ('collection_stage', '=', self.env.context['collection_stage'])])
                # 在催收员今日已分配订单数量＜“今日进件上限”
                user_ids = []
                for points_id in points_ids:
                    if points_id.max_daily_intake > self.env['collector.link.order.record'].sudo().search_count([('collector_id', '=', points_id.user_id.id), ('allot_date', '=', date.today())]):
                        user_ids.append(points_id.user_id.id)
                domain.append(('id', 'in', user_ids))
            if self.env.context['bill_search'] == 'collection.order.pending':
                user_contact_ids = self.env['user.contact'].sudo().search([('collection_order_id', '=', self.env.context['res_id'])]).mapped('user_id').ids
                user_contact_ids.append(self.env.user.id)
                domain.append(('id', 'in', user_contact_ids))

        return super(ResUsers, self)._search(args + domain, offset, limit, order, access_rights_uid=access_rights_uid)
