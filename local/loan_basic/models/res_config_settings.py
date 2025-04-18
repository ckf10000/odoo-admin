
from odoo import models, fields, api, _
 
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    oss_access_key = fields.Char(config_parameter='oss.access_key')
    oss_secret_key = fields.Char(config_parameter='oss.secret_key')
    oss_endpoint = fields.Char(config_parameter='oss.endpoint')
    oss_bucket = fields.Char(config_parameter='oss.bucket')


    loan_api_base_url = fields.Char(config_parameter='loan_api.base.url')