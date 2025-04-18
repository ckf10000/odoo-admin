import logging
from odoo import models, fields, api, exceptions
from ..utils import config

_logger = logging.getLogger(__name__)


class JointLoanMatrix(models.Model):
    """
    jlm_name: string，not null，最大长度 = MAX_length_jlm_name
    status: bool, not null，TRUE = 启用，FALSE = 停用
    """
    _name = 'joint.loan.matrix'
    _description = 'Joint Loan Matrix'
    _table = 'T_joint_loan_matrix'
    _inherit = ['loan.basic.model']
    _rec_name = 'jlm_name'

    jlm_name = fields.Char(string='矩阵名称', required=True, size=config.JointLoanMatrixConfig.MAX_length_jlm_name)
    matrix_code = fields.Char(string='矩阵ID', required=True, index=True)
    status = fields.Boolean(string='状态', required=True, default=True)

    app_ids = fields.One2many('loan.app', 'matrix_id', string='App名称')
    product_ids = fields.One2many('loan.product', 'matrix_id', string='产品名称')

    rule_ids = fields.One2many('joint.loan.setting', 'matrix_id', string='共贷配置')

    @api.model
    def _check_data(self, data):
        """
        检查产品信息, 并一次性抛出所有错误
        """
        errors = []
        exist_names = {}

        for rec in self.search([]):
            exist_names.setdefault(rec.jlm_name, []).append(rec.id)

        # 名称校验
        name = data.get('jlm_name')
        if name.count('  '):
            errors.append('共贷矩阵名称不能有连续空格, 请调整')
        
        exist_ids = exist_names.get(name, [])
        if exist_ids and data.get('id') not in exist_ids:
            errors.append('共贷矩阵名称已使用，请更换名称')

        if errors:
            raise exceptions.ValidationError(self.format_action_error(errors))

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            self._check_data(val)
            val['matrix_code'] = self.env['ir.sequence'].next_by_code('loan_matrix_code_seq')
        objs = super().create(vals_list)
        return objs
    
    def write(self, vals):
        res = super().write(vals)
        if 'rule_ids' in vals:
            self.rule_ids.check_all_data(self.id)
        return res
    
