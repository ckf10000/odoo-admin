import logging
from odoo import models, fields, api
from . import enums


_logger = logging.getLogger(__name__)


class LoanOrder(models.Model):
    _description = '订单管理'
    _inherit = ['loan.order']
    _table = 'T_order'




    

    