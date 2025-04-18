import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class JointLoanSetting(models.Model):
    _name = 'joint.loan.setting'
    _description = 'Join Loan Setting'
    _order = 'from_date, to_date'
    _inherit = ['loan.basic.model']
    _table = 'T_joint_loan_setting'

    matrix_id = fields.Many2one(
        'joint.loan.matrix', 
        string='共贷矩阵', 
        required=True, 
        ondelete='restrict', 
        index=True,
        default=lambda self: self.env['joint.loan.matrix'].search([], limit=1)
    )
    from_date = fields.Integer('距放款日期开始')
    to_date = fields.Integer('距放款日期结束')
    display_date = fields.Char('距第一笔放款日期差', compute='_compute_display_date')
    max_num_on_loan = fields.Integer('最高可在贷笔数')
    max_num_new_product_daily = fields.Integer('每天可在贷新产品数量')
    max_num_push_daily = fields.Integer('每天新产品推单上限')

    @api.depends('from_date', 'to_date')
    def _compute_display_date(self):
        for record in self:
            if  record.to_date == -1:
                record.display_date = '纯新户'
            elif not record.to_date:
                record.display_date = f"≥{record.from_date}"    # --by zhouhanlin 修改前端显示问题
            else:
                record.display_date = f"{record.from_date} - {record.to_date}"

    def action_update(self):
        """
        列表点击修改按钮，根据选择的共贷矩阵，更新该矩阵下面所有的配置
        """
        matrix_id = None
        for domain in self.env.context.get('active_domain', []):
            if domain[0] == 'matrix_id':
                matrix_id = domain[2]
                break
        if not matrix_id:
            return  {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': "提示",
                    'type': 'warning',
                    'message': "请选择共贷矩阵",
                    'sticky': False,
                }
            }
        return {
            'name': '编辑共贷配置',
            'type': 'ir.actions.act_window',
            'res_model': 'joint.loan.matrix',
            'res_id': matrix_id,
            'view_mode': 'form',
            'view_id': self.env.ref('loan_market.form_joint_loan_matrix_update_config').id,
            'target': 'new'
        }

    def check_all_data(self, matrix_id):
        """
        数据校验
        """
        objs = self.search([('matrix_id', '=', matrix_id)])
        errors = []
        
        end = -1
        count = len(objs)
        for dx, obj in enumerate(objs):
            # 纯新户
            if dx == 0:
                if obj.from_date != -1 or obj.to_date != -1:
                    # raise exceptions.ValidationError(f"请设置纯新户，纯新户的距放款日期开始和结束都为0")
                    errors.append(f"请设置纯新户，纯新户的距放款日期开始和结束都为-1")
            else: 
                # 校验日期差是否连续
                if obj.from_date != end + 1:
                    errors.append(f"{obj.display_date}: ：距放款日期必须连续")

                # 非最后一个
                if dx < count-1:
                    if obj.from_date > obj.to_date:
                        errors.append(f"{obj.display_date}：距放款日期结束必须≥开始")
                    elif obj.to_date > 999:
                        errors.append(f"{obj.display_date}: 距放款日期结束请输整数值(0-999)")
                else:
                    if obj.to_date != 0:
                        errors.append(f"{obj.display_date}: 配置项日期结束必须为0")
                
                end = obj.to_date

            if obj.max_num_on_loan < 0:
                errors.append(f"{obj.display_date}: 最高可在贷笔数请输入≥0的整数")
            if obj.max_num_new_product_daily < 0:
                errors.append(f"{obj.display_date}: 每天可在贷新产品数量请输入≥0的整数")
            if obj.max_num_push_daily < 0:
                errors.append(f"{obj.display_date}: 每天可在贷新产品数量请输入≥0的整数")

        if errors:
            raise exceptions.ValidationError(self.format_action_error(errors))

    @api.model_create_multi
    def create(self, vals_list):
        objs = super().create(vals_list)
        self.check_all_data(objs.matrix_id.id)
        return objs
    
    @api.onchange('matrix_id')
    def _onchange_matrix_id(self):

        matrix_rules = self.matrix_id.rule_ids
        new_count = len(matrix_rules)

        if new_count <= 1:
            self.from_date = -1
            self.to_date = -1
        else:
            last_rule = matrix_rules[new_count-2]
            self.from_date = last_rule.to_date + 1
        


