import logging  
from odoo import models, fields, api  
from odoo.exceptions import ValidationError, UserError  

_logger = logging.getLogger(__name__)  

class CollectorLinkOrderRecord(models.Model):  
    _name = 'collector.link.order.record'  
    _table = "C_link_order_record"  
    _inherit = ['loan.basic.model']  
    _description = '催收员分单记录'  

    collector_id = fields.Many2one('res.users', string='催收员', required=True)  
    allot_date = fields.Date(string='分单日期', default=fields.Date.context_today)  
    collection_order_id = fields.Many2one('collection.order', string='关联催收订单')  

    @api.model  
    def create(self, values):  
        """新增记录时反写到对应"""  
        # 确保 collector_id 存在  
        if 'collector_id' not in values:  
            raise ValidationError("必须指定催收员。")  

        res_id = super(CollectorLinkOrderRecord, self).create(values)  

        # 获取相关的 collection.points 记录  
        points_id = self.env['collection.points'].sudo().search([('user_id', '=', res_id.collector_id.id)], limit=1)  
        if points_id:  
            points_id.sudo().write({'today_pending_qty': points_id.today_pending_qty + 1})  
        else:  
            _logger.warning("未找到与催收员相关的 collection.points 记录。")  

        return res_id