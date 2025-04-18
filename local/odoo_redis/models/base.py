from odoo import models, api, tools
from odoo.http import request


class Base(models.AbstractModel):
    _inherit = 'base'

    @property
    def redis(self):
        return request.redis
