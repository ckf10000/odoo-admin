import logging
from odoo import models, fields, api, exceptions, _
from . import enums


_logger = logging.getLogger(__name__)


class DerateRecord(models.Model):
    _name = 'derate.record'
    _description = '减免记录'
    _inherit = ['loan.basic.model']
    _table = 'F_derate_record'

    order_id = fields.Many2one('loan.order', string="订单编号", required=True, index=True, auto_join=True)
    order_no = fields.Char(string='订单编号', related="order_id.order_no")
    loan_uid = fields.Integer('UserID', related='order_id.loan_uid')
    loan_user_name = fields.Char(string='姓名', related='order_id.loan_user_name')
    loan_user_phone = fields.Char(string='手机号码', related="order_id.loan_user_phone")
    app_id = fields.Many2one('loan.app', string='APP名称', related="order_id.app_id")
    app_version = fields.Char(string='APP版本', related="order_id.app_version")
    product_id = fields.Many2one('loan.product', string='产品名称', related="order_id.product_id")
    order_apply_time = fields.Datetime(string='申请时间', related="order_id.apply_time")
    order_status = fields.Selection(related="order_id.order_status", store=True, index=True)

    loan_cycle = fields.Char(string='期数', default="1/1")

    order_pending_amount = fields.Float(string='挂账金额')
    max_derate_amount = fields.Float(string='最大可减免金额') 

    derate_no = fields.Char(string='减免编号', required=True, index=True)
    derate_amount = fields.Float(string='减免金额', digits=(16, 2))
    apply_user_id = fields.Many2one('res.users', string='申请人')
    apply_reason = fields.Text(string='申请理由')
    apply_time = fields.Datetime(string='申请时间')
    derate_type = fields.Selection(selection=enums.DERATE_TYPE, string='减免类型')
    valid_time = fields.Datetime(string='有效期截止时间', index=True)
    is_effective = fields.Boolean(string='是否生效', default=False)

    col_approval_status = fields.Selection(selection=enums.DERATE_APPROVAL_STATUS, string='催收审核状态', default="0")
    col_approval_user_id = fields.Many2one('res.users', string='催收审核人员')
    col_approval_time = fields.Datetime(string='催收审核时间')
    col_approval_remark = fields.Text(string='催收备注')

    fin_approval_status = fields.Selection(selection=enums.DERATE_APPROVAL_STATUS, string='财务审核状态', default="0")
    fin_approval_user_id = fields.Many2one('res.users', string='财务审核人员')
    fin_approval_time = fields.Datetime(string='财务审核时间')
    fin_approval_remark = fields.Text(string='财务备注')

    @api.model
    def task_lose_efficacy(self):
        """
        定时任务, 将已过期的减免记录失效
        """
        now = fields.Datetime.now()
        platform_data = []
        for rec in self.search([('order_status', '=', '7'), ('valid_time', '<', now), ('derate_type', '=', '1'), ('is_effective', '=', True)]):
            rec.write({'is_effective': False})
            platform_data.append({
                "order_id": rec.order_id.id,
                "flow_type": enums.FLOW_TYPE[1][0],
                "flow_amount": rec.derate_amount,
                "trade_type": enums.TRADE_TYPE[21][0],
                "flow_time": now
            })
            rec.order_id.update_order_status(now)
        if platform_data:
            self.env['platform.flow'].create(platform_data)

    @api.model
    def _check_derate_data(self, data):
        """
        检查减免数据
        """
        order_id = data['order_id']
        exist_rec = self.env[self._name].search([('order_id', '=', order_id), '|', ('col_approval_status', '=', '1'), ('fin_approval_status', '=', '1')])
        _logger.info("exist_rec: %s" % exist_rec)
        if exist_rec:
            stage = "催收" if exist_rec[0].col_approval_status == 1 else "财务"
            raise exceptions.ValidationError(f"存在{stage}未完成审核的减免记录, 完成后才能再次减免!")

        errors = [] 
        derate_amount, max_derate_amount = data['derate_amount'], data['max_derate_amount']
        if derate_amount <= 0:
            errors.append('减免金额>0')

        if derate_amount > max_derate_amount:
            errors.append('减免金额≤最大可减免金额')
            
        if errors:
            raise exceptions.ValidationError(self.format_action_error(errors))

    @api.model
    def create(self, vals):
        self._check_derate_data(vals)

        order = self.env['loan.order'].browse(vals['order_id'])
        vals.update({
            "derate_no": self.env['ir.sequence'].next_by_code('derate_record_seq'),
            'app_version': order.app_version,
            'apply_user_id': self.env.user.id,
            'apply_time': fields.Datetime.now()
        })
        obj = super(DerateRecord, self).create(vals)
        return obj
    
    def fin_approval(self, approval_data):
        """
        财务减免审核
        """
        self.write(approval_data)
        if self.fin_approval_status == "2":
            self.env['platform.flow'].create({
                "order_id": self.order_id.id,
                "flow_type": enums.FLOW_TYPE[0][0],
                "flow_amount": self.derate_amount,
                "trade_type": enums.TRADE_TYPE[20][0],
                "flow_time": self.fin_approval_time
            })

            repay_order = self.order_id.get_repay_order()
            repay_order.update_repay_status(self.fin_approval_time)

    def col_approval(self, approval_data):
        """
        催收减免审核
        """
        self.write(approval_data)
        if self.col_approval_status == "2":
            self.action_fin_create()

    def action_fin_create(self):
        """
        财务创建减免记录
        """
        auto_pass = self.env['loan.order.settings'].get_param('fin_derate_auto_approval', False)
        if auto_pass:
            max_amount = self.env['loan.order.settings'].get_param('fin_derate_auto_approval_max_amount', 0)
            if self.derate_amount > max_amount:
                return
            
            self.fin_approval({
                'fin_approval_status': '2',
                'fin_approval_user_id': self.env.user.id,
                'fin_approval_time': self.apply_time,
                'fin_approval_remark': '自动审核通过',
                'is_effective': True
            })
    
    def _action_show_derate_setting_wizard(self, context={}):
        context.update({
            'dialog_size': self._action_default_size(),
        })
        return {
            'name': '自动审核配置' if self.env.user.lang == "zh_CN" else "Auto Review Configuration",
            'type': 'ir.actions.act_window',
            'res_model': "derate.record.setting.wizard",
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.wizard_derate_setting').id,
            'target': 'new',
            'context': context
        }

    def action_fin_derate_setting(self):
        """
        财务减免设置
        """
        auto_pass = self.env['loan.order.settings'].get_param('fin_derate_auto_approval', False)
        max_amount = self.env['loan.order.settings'].get_param('fin_derate_auto_approval_max_amount', 0)
        context = {
            'default_setting_type': '1',
            'default_auto_pass': auto_pass,
            'default_max_amount': max_amount,
        }
        return self._action_show_derate_setting_wizard(context)

    def _action_show_approval_wizard(self, action_name, context={}):
        context.update({
            'dialog_size': self._action_default_size(),
            'default_derate_id': self.id,
            **context
        })
        return {
            'name': action_name,
            'type': 'ir.actions.act_window',
            'res_model': "derate.record.approval.wizard",
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.wizard_fin_derate_approval').id,
            'target': 'new',
            'context': context
        }
    
    def action_show_fin_approval(self):
        approve_flag = self.env.context.get('flag', 0)
        name = '审核通过' if approve_flag else '审核拒绝',
        return self._action_show_approval_wizard(name, {
            'default_approval_type': "1",
            'default_approval_result': "2" if approve_flag else "3",
            'default_desc': f"{self.derate_amount}, 否确定审核{'通过' if approve_flag else '拒绝'}?"
        })
    
    def _action_show_batch_approval_wizard(self, context):
        lang = self.env.user.lang
        amount = round(sum(self.mapped(lambda x: x.derate_amount)), 2)
        text = "合计申请减免金额" if lang == "zh_CN" else "Aplication of Amount Remission"
        context = {
            'dialog_size': self._action_default_size(),
            'default_derate_record_ids': self.ids,
            'default_desc': f"{len(self.ids)}, {text}:{amount}",
            **context
        }
        return {
            'name': '批量审核' if lang == "zh_CN" else "Batch Review",
            'type': 'ir.actions.act_window',
            'res_model': "derate.record.batch.approval.wizard",
            'view_mode': 'form',
            'view_id': self.env.ref('loan_financial.wizard_fin_derate_batch_approval').id,
            'target': 'new',
            'context': context
        }
    
    def action_fin_derate_batch_approval(self):   
        if not self.ids:
            raise exceptions.UserError('请先勾选需要批量审核的订单！')
        
        return self._action_show_batch_approval_wizard({'default_approval_type': '1'})
        

class DerateRecordSettingWizard(models.TransientModel):
    _name = 'derate.record.setting.wizard'
    _description = '减免记录配置向导'
    _inherit = ['loan.basic.model']

    setting_type = fields.Selection([('1', '财务'), ('2', '催收')], string="设置类型")
    auto_pass = fields.Boolean(string="自动审核")
    max_amount = fields.Integer(string="最大减免金额")

    def action_setting(self):
        if self.setting_type == '1':
            key1 = "fin_derate_auto_approval"
            key2 = "fin_derate_auto_approval_max_amount"
        else:
            key1 = "col_derate_auto_approval"
            key2 = "col_derate_auto_approval_max_amount"

        self.env['loan.order.settings'].set_param(key1, self.auto_pass)
        self.env['loan.order.settings'].set_param(key2, self.max_amount)

        if not self.auto_pass:
            return 
        
        # 自动审核
        if self.setting_type == "1":
            derate_rec_data = {
                'fin_approval_status': "2",
                'fin_approval_user_id': self.env.user.id,
                'fin_approval_time': fields.Datetime.now(),
                'fin_approval_remark': '自动审核通过',
                'is_effective': True 
            }
            for obj in self.env['derate.record'].search([('fin_approval_status', '=', '1'), ('derate_amount', '<=', self.max_amount)]):
                obj.fin_approval(derate_rec_data)
        else:
            derate_rec_data = {
                'col_approval_status': "2",
                'col_approval_user_id': self.env.user.id,
                'col_approval_time': fields.Datetime.now(),
                'col_approval_remark': '自动审核通过',
                'fin_approval_status': '1' 
            }
            for obj in self.env['derate.record'].search([('col_approval_status', '=', '1'), ('derate_amount', '<=', self.max_amount)]):
                obj.col_approval(derate_rec_data)
        return 


class DerateRecordApprovalWizard(models.TransientModel):
    _name = 'derate.record.approval.wizard'
    _description = '减免记录审核向导'
    _inherit = ['loan.basic.model']

    approval_type = fields.Selection([('1', '财务'), ('2', '催收')], string="审核类型")
    derate_id = fields.Many2one('derate.record', string="减免记录", required=True)
    desc = fields.Text(string='审核描述')
    approval_result = fields.Selection([('2', '通过'), ('3', '拒绝')], string='批量审核')
    remark = fields.Text(string='备注', required=True)

    def action_approval(self):
        """
        财务审核
        """
        if self.approval_type == "1":
            derate_rec_data = {
                'fin_approval_status': self.approval_result,
                'fin_approval_user_id': self.env.user.id,
                'fin_approval_time': fields.Datetime.now(),
                'fin_approval_remark': self.remark,
                'is_effective': True if self.approval_result == "2" else False
            }
            self.derate_id.fin_approval(derate_rec_data)
        else:
            derate_rec_data = {
                'col_approval_status': self.approval_result,
                'col_approval_user_id': self.env.user.id,
                'col_approval_time': fields.Datetime.now(),
                'col_approval_remark': self.remark,
                'fin_approval_status': '1' if self.approval_result == "2" else '0',
            }
            self.derate_id.col_approval(derate_rec_data)
            

class DerateRecordBatchApprovalWizard(models.TransientModel):
    _name = 'derate.record.batch.approval.wizard'
    _description = '批量审核向导'
    _inherit = ['loan.basic.model']

    approval_type = fields.Selection([('1', '财务'), ('2', '催收')], string="审核类型")
    derate_record_ids = fields.Json(string='减免记录', required=True)
    desc = fields.Char(string='已选择订单数量')
    approval_result = fields.Selection([('2', _('Pass')), ('3', _('Refuse'))], string='批量审核')
    remark = fields.Text(string='备注', required=True)

    @api.onchange("approval_result")
    def _onchange_approval_result(self):
        if self.approval_result == '2':
            self.remark = '无异常通过' if self.env.user.lang == "zh_CN" else "Cleared without any issues"
        else:
            self.remark = ''

    def action_approval(self):
        """
        财务审核
        """
        if self.approval_type == "1":
            derate_rec_data = {
                'fin_approval_status': self.approval_result,
                'fin_approval_user_id': self.env.user.id,
                'fin_approval_time': fields.Datetime.now(),
                'fin_approval_remark': self.remark,
                'is_effective': True if self.approval_result == "2" else False
            }
        else:
            derate_rec_data = {
                'col_approval_status': self.approval_result,
                'col_approval_user_id': self.env.user.id,
                'col_approval_time': fields.Datetime.now(),
                'col_approval_remark': self.remark,
                'fin_approval_status': '1' if self.approval_result == "2" else '0',
            }

        for derate_record in self.env['derate.record'].browse(self.derate_record_ids):
            if self.approval_type == "1":
                derate_record.fin_approval(derate_rec_data)
            else:
                derate_record.col_approval(derate_rec_data)