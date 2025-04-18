import logging
from odoo import models, fields, _, api, exceptions

_logger = logging.getLogger(__name__)


class LoanSettingTeam(models.Model):
    _name = 'loan.settings.team'
    _description = 'Team'
    _table = 'R_team'
    _inherit = 'loan.basic.model'
    _parent_store = True
    _parent_name= 'parent_id'
    _rec_name = 'name'
    _order = 'sort asc'

    sequence = fields.Char(string=_('TeamID'), index=True, required=True)
    sort = fields.Integer(string=_('Sorted'))
    name = fields.Char(string=_('Teamname'))
    active = fields.Boolean(string=_('Enable'), default=True)
    parent_id = fields.Many2one('loan.settings.team', string=_('Parent TeamID'), domain="[('merchant_id', '=', merchant_id)]",
                                required=False, index=True, auto_join=True, ondelete="restrict")
    child_ids = fields.One2many('loan.settings.team', 'parent_id', string=_('Child TeamID'))
    parent_path = fields.Char(index=True, unaccent=False)
    merchant_id = fields.Many2one('loan.settings.merchant', string=_('Belong Merchant'), required=True, index=True)
    company_id = fields.Many2one('res.company', string='Company', related="merchant_id.company_id", store=True, index=True)

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            existing = self.search([('name', '=', record.name), ('id', '!=', record.id)], limit=1)
            if existing:
                msg = "团队名称必须唯一" if self.env.user.lang == "zh_CN" else "The team name must be unique."
                raise exceptions.ValidationError(msg)

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise exceptions.ValidationError(_('不能选择子级作为上级'))
        
    @api.onchange('merchant_id')
    def _onchange_merchant_id(self):
        self.parent_id = False
        
    def create(self, vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('team_code_seq')
        return super(LoanSettingTeam, self).create(vals)
    
    def write(self, vals):
        res = super(LoanSettingTeam, self).write(vals)
        if "merchant_id" in vals:
            if self.child_ids:
                self.child_ids.write({"merchant_id": vals["merchant_id"]})
        return res