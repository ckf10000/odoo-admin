import logging
from odoo import models, fields, api, exceptions
from . import enums


_logger = logging.getLogger(__name__)


class DerateRecord(models.Model):
    _description = '减免记录'
    _inherit = ['derate.record']

    collection_stage_setting_id = fields.Many2one(
        "collection.stage.setting", string="催收阶段"
    )

    def action_col_create(self):
        """
        催收创建减免记录
        """
        auto_pass = self.env['loan.order.settings'].get_param('col_derate_auto_approval', False)
        if auto_pass:
            max_amount = self.env['loan.order.settings'].get_param('col_derate_auto_approval_max_amount', 0)
            if self.derate_amount > max_amount:
                return
            
            self.col_approval({
                'col_approval_status': '2',
                'col_approval_user_id': self.env.user.id,
                'col_approval_time': self.apply_time,
                'col_approval_remark': '自动审核通过',
                'fin_approval_status': "1"
            })

    def action_show_col_approval_wizard(self):
        approve_flag = self.env.context.get('flag', 0)
        pass_text = "审核通过" if self.env.user.lang == "zh_CN" else "Approval Pass"
        refuse_text = "审核拒绝" if self.env.user.lang == "zh_CN" else "Approval Refuse"
        desc = "是否确定审核" if self.env.user.lang == "zh_CN" else "Are you sure to confirm the review as"
        result_pass = '通过' if self.env.user.lang == "zh_CN" else "Pass"
        result_refuse = "拒绝" if self.env.user.lang == "zh_CN" else "Refuse"
        result = result_pass if approve_flag else result_refuse
        default_desc = f"{self.derate_amount}, {desc} {result}?"
        return {
            'name': pass_text if approve_flag else refuse_text,
            'type': 'ir.actions.act_window',
            'res_model': "derate.record.approval.wizard",
            'view_mode': 'form',
            'view_id': self.env.ref('loan_collection.wizard_col_derate_approval').id,
            'target': 'new',
            'context': {
                'dialog_size': self._action_default_size(),
                'default_derate_id': self.id,
                'default_status': "2" if approve_flag else "3",
                'default_desc': default_desc
            }
        }
    
    def action_col_derate_setting(self):
        """
        财务减免设置
        """
        auto_pass = self.env['loan.order.settings'].get_param('col_derate_auto_approval', False)
        max_amount = self.env['loan.order.settings'].get_param('col_derate_auto_approval_max_amount', 0)
        context = {
            'default_setting_type': '2',
            'default_auto_pass': auto_pass,
            'default_max_amount': max_amount,
        }
        return self._action_show_derate_setting_wizard(context)
    
    def action_col_derate_batch_approval(self):   
        if not self.ids:
            msg = "请先勾选需要批量审核的订单！" if self.env.user.lang == "zh_CN" else \
                "Please first check the orders that require batch review"
            raise exceptions.UserError(msg)
        return self._action_show_batch_approval_wizard({'default_approval_type': '2'})
    
    def action_show_col_approval(self):
        approve_flag = self.env.context.get('flag', 0)
        pass_text = "审核通过" if self.env.user.lang == "zh_CN" else "Approval Pass"
        refuse_text = "审核拒绝" if self.env.user.lang == "zh_CN" else "Approval Refuse"
        name = pass_text if approve_flag else refuse_text
        desc = "是否确定审核" if self.env.user.lang == "zh_CN" else "Are you sure to confirm the review as"
        result_pass = '通过' if self.env.user.lang == "zh_CN" else "Pass"
        result_refuse = "拒绝" if self.env.user.lang == "zh_CN" else "Refuse"
        result = result_pass if approve_flag else result_refuse
        default_desc = f"{self.derate_amount}, {desc} {result}?"
        return self._action_show_approval_wizard(name, {
            'default_approval_type': "2",
            'default_approval_result': "2" if approve_flag else "3",
            'default_desc': default_desc
        })
 