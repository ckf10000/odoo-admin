import logging
from odoo import models, fields, api, exceptions


_logger = logging.getLogger(__name__)


class LoanOrder(models.Model):

    _description = '订单管理'
    _inherit = ['loan.order']
    _rec_name = 'order_no'

    collection_order_ids = fields.One2many(
        "collection.order", "loan_order_id", string="催收记录"
    )
    collection_order_id = fields.Many2one(
        "collection.order", string="催收记录", compute="_compute_collection_data", store=True
    )

    collection_stage_setting_id = fields.Many2one(
        "collection.stage.setting", string="催收阶段", related="collection_order_id.collection_stage_setting_id"
    )
    collector_id = fields.Many2one(
        "res.users", string="催收员", related="collection_order_id.collector_id"
    )

    collection_record_ids = fields.One2many("history.collection.record", string="催收记录", related="collection_order_id.history_collection_record_ids")

    @api.depends('collection_order_ids')
    def _compute_collection_data(self):
        for rec in self:
            rec.collection_order_id = rec.collection_order_ids[-1] if rec.collection_order_ids else False

    def action_show_collection_record(self):
        self.ensure_one()
        return {
            'name': '催收记录' if self.env.user.lang == "zh_CN" else "Collection Record",
            'type': 'ir.actions.act_window',
            'res_model': 'history.collection.record',
            'view_mode': 'tree',
            'view_id': self.env.ref('loan_collection.list_collection_record').id,
            'domain': [('collection_order_id', '=', self.collection_order_id.id)],
            'target': 'new'
        }