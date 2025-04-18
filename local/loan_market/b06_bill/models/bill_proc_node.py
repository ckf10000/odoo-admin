import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class BillProcNode(models.Model):
    _name = 'bill.proc.node'
    _description = 'BillProcNode'
    _inherit = ['loan.basic.model']
    _table = 'T_bill_proc_node'

    enum_code = fields.Integer(string='枚举编码', required=True)
    node_name = fields.Char(string='节点名称', required=True)