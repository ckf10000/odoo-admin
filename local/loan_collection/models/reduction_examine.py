import logging
from odoo import models, fields, api, exceptions
from datetime import datetime


class LoanReductionExamine(models.Model):
    _name = 'loan.reduction.examine'
    _inherit = ['loan.order', 'loan.basic.model']
    _description = '金额减免审核'

    code = fields.Char(string='减免申请编号', default=lambda self: self.env['ir.sequence'].next_by_code('loan.reduction.examine'))
    order_id = fields.Many2one('loan.order', string='关联订单')
    order_no = fields.Char(string='订单编号', releated='order_id.order_no')
    product_id = fields.Many2one('loan.product', string='产品')
    bill_id = fields.Many2one('loan.bill')
    product_name = fields.Char(string='产品名称', index=True, releated='product_id.product_name')
    application_time = fields.Datetime(string='申请时间')
    derate_amount = fields.Float(string='减免金额', digits=(16, 2))

    collection_phase_id = fields.Char(string='催收阶段')
    reduction_type = fields.Selection([
        ('permanent', '永久性减免'),
        ('validity_reduction', '有效期减免')
    ], string='减免类型')
    validity_date = fields.Datetime(string='有效期')
    audit_time = fields.Datetime(string='催收审核时间')
    collection_audit_time = fields.Datetime(string='审核通过操作时间(催收)')
    flow_type = fields.Selection([
        ('draft', '草稿'),
        ('audit', '已通过'),
        ('fail', '已拒绝')
    ], string='金额减免流程')

    # 催收模块 新增字段
    resource_model = fields.Selection([
        ('loan', '财务'),
        ('collection', '催收')
    ], string='所属模块')
    collection_flow_status = fields.Selection([
        ('draft', '草稿'),
        ('audit', '已通过'),
        ('fail', '已拒绝')
    ], string='催收状态', default='draft')
    application_argument = fields.Text(string='申请理由')
    current_total_cycle = fields.Char(string='借款当前周期/总周期', default='1/1')  # 固定展示为1/1
    max_annul_amount = fields.Float(string='最大可减免金额', digits=(16, 2))
    examine_remark = fields.Text(string='减免审核备注')

    # @api.constrains('derate_amount')
    # def _check_annul_amount(self):
    #     if not 0 < self.derate_amount <= self.max_annul_amount:
    #         raise exceptions.ValidationError('0＜减免金额≤最多可减免金额')

    def agree_action(self):
        """
        通过
        """
        form_view_id = self.env.ref('loan_collection.reduction_examine_wizard_audit_fail_form')
        pass_text = "审核通过" if self.env.user.lang == "zh_CN" else "Approval Pass"
        display_info = '申请减免金额：%s，是否确定审核通过？' % self.derate_amount if self.env.user.lang == "zh_CN" else \
            "Aplication of Amount Remission: %s, Are you sure to approve the review?" % self.derate_amount
        return {
            'name': pass_text,
            'type': 'ir.actions.act_window',
            'res_model': 'reduction.examine.wizard',
            'view_mode': 'form',
            'views': [(form_view_id.id, 'form')],
            'target': 'new',
            'context': {
                'default_selected_ids': len(self),
                'default_flow_type': 'audit',
                'default_total_annul_amount': self.derate_amount,
                'default_display_info': display_info,
                'dialog_size': self._action_default_size(), **self._action_default_data()}
        }

    def repulse_action(self):
        """
        拒绝
        """
        form_view_id = self.env.ref('loan_collection.reduction_examine_wizard_audit_fail_form')
        refuse_text = "审核拒绝" if self.env.user.lang == "zh_CN" else "Approval Refuse"
        display_info = '申请减免金额：%s，是否确定拒绝审核？' % self.derate_amount if self.env.user.lang == "zh_CN" else \
            "Aplication of Amount Remission: %s, Are you sure to refuse the review?" % self.derate_amount
        return {
            'name': refuse_text,
            'type': 'ir.actions.act_window',
            'res_model': 'reduction.examine.wizard',
            'view_mode': 'form',
            'views': [(form_view_id.id, 'form')],
            'target': 'new',
            'context': {
                'default_selected_ids': len(self),
                'default_flow_type': 'fail',
                'default_total_annul_amount': self.derate_amount,
                'default_display_info': display_info,
                'dialog_size': self._action_default_size(), **self._action_default_data()}
        }

    # def action_submit(self):
    #     """
    #     提交
    #     """
    #

    def action_batch_audit(self):
        """
        批量审核
        """
        lang = self.env.user.lang
        if len(self) == 0:
            msg = "请先勾选需要批量审核的订单！" if lang == "zh_CN" else \
                "Please first check the orders that require batch review"
            raise exceptions.ValidationError(msg)
        else:
            form_view_id = self.env.ref('loan_collection.reduction_examine_wizard_batch_form')
            return {
                'name': '批量审核' if lang == "zh_CN" else "Batch Review",
                'type': 'ir.actions.act_window',
                'res_model': 'reduction.examine.wizard',
                'view_mode': 'form',
                'views': [(form_view_id.id, 'form')],
                'target': 'new',
                'context': {
                    'default_selected_ids': len(self),
                    'default_flow_type': 'batch',
                    'default_total_annul_amount': sum(self.mapped('derate_amount')),
                    'default_display_info': '已选择订单数量：%s，合计申请减免金额：%s' % (len(self), sum(self.mapped('derate_amount'))),
                    'dialog_size': self._action_default_size(), **self._action_default_data()}
            }

    def action_auto_audit_setting(self):
        """
        自动审核设置
        """

        form_view_id = self.env.ref('loan_collection.auto_examine_form')
        return {
            'name': '自动审核配置' if self.env.user.lang == "zh_CN" else "Auto Review Configuration",
            'type': 'ir.actions.act_window',
            'res_model': 'auto.examine',
            'res_id': self.env['auto.examine'].search([], limit=1).id,
            'view_mode': 'form',
            'views': [(form_view_id.id, 'form')],
            'target': 'new',
            'context': {'dialog_size': self._action_default_size(), **self._action_default_data()}}

    def create_examine_record(self):
        """创建金额减免记录"""
        create_data = []
        for record in self:
            create_data.append({
                'collection_examine_id': record.id,
                'user_id': record.user_id.id,
                'code': record.code,
                'order_id': record.order_id.id,
                'product_id': record.product_id.id,
                'bill_id': record.bill_id.id,
                'application_time': record.application_time,
                'derate_amount': record.derate_amount,
                'collection_phase_id': record.collection_phase_id,
                'reduction_type': record.reduction_type,
                'validity_date': record.validity_date,
                'audit_time': record.audit_time,
                'collection_audit_time': record.collection_audit_time,
                'flow_type': record.flow_type,
                'resource_model': record.resource_model,
                'collection_flow_status': record.collection_flow_status,
                'application_argument': record.application_argument,
                'current_total_cycle': record.current_total_cycle,
                'max_annul_amount': record.max_annul_amount,
                'reduction_remark': record.reduction_remark,
                'finance_remark': record.finance_remark,
                'finance_user_id': record.finance_user_id,
            })
        if create_data:
            self.env['collection.reduction.examine.record'].sudo().create(create_data)

    def action_server_reduction_examine(self):
        """
        金额减免管理action
        """
        # 新增resource_model字段 区分催收、财务模块
        context = self.env.context
        tree_view_id = self.env.ref('loan_collection.loan_reduction_examine_list')
        domain = [('flow_type', '=', 'draft'), ('resource_model', '=', 'loan')]
        search_view_id = self.env.ref('loan_collection.loan_reduction_examine_search')
        action_id = self.env.ref('loan_collection.loan_reduction_examine_action')
        return {
            'id': action_id.id,
            'type': 'ir.actions.act_window',
            'name': '金额减免管理',
            'res_model': self._name,
            'view_mode': 'tree',
            'domain': domain,
            'views': [(tree_view_id.id, 'list')],
            'search_view_id': [search_view_id.id],
            'target': 'current',
            'context': dict(context)
        }

    def action_server_reduction_examine_collection(self):
        """
        金额减免管理action(催收)
        """
        # 新增resource_model字段 区分催收、财务模块
        context = self.env.context
        tree_view_id = self.env.ref('loan_collection.loan_reduction_examine_list')
        domain = [('collection_flow_status', '=', 'draft'), ('resource_model', '=', 'collection')]
        search_view_id = self.env.ref('loan_collection.loan_reduction_examine_search')
        action_id = self.env.ref('loan_collection.loan_reduction_examine_action')
        return {
            'id': action_id.id,
            'type': 'ir.actions.act_window',
            'name': '金额减免管理',
            'res_model': self._name,
            'view_mode': 'tree',
            'domain': domain,
            'views': [(tree_view_id.id, 'list')],
            'search_view_id': [search_view_id.id],
            'target': 'current',
            'context': dict(context)
        }

    @api.model_create_multi
    def create(self, vals_list):
        """
        增加自动审核逻辑
        """
        records = super(LoanReductionExamine, self).create(vals_list)
        auto_examine = self.env['auto.examine'].search([], limit=1).auto_examine
        if auto_examine:
            records.write({
                'resource_model': 'loan',
                'collection_flow_status': 'audit',
                'collection_audit_time': datetime.now(),
                'flow_type': 'draft',
                'reduction_remark': '系统通过'
            })
            records.create_examine_record()
        return records

    @api.constrains('resource_model')
    def _auto_loan_audit(self):
        """已经转为财务的且开启了自动审核单据处理"""
        if self.resource_model == 'loan':
            auto_examine = self.env['auto.examine'].search([], limit=1)
            if auto_examine:
                self.write({
                    'finance_audit_date': datetime.now(),
                    'finance_user_id': self.env.user.id,
                    'finance_user_char': self.env.user.name,
                    'finance_remark': '系统通过',
                    'flow_type': 'draft',
                })
                self.create_examine_record()
                # 如果为永久性减免或者有效期减免且当前时间小于有效期且剩余金额等于0
                if self.reduction_type == 'permanent' or self.reduction_type == 'validity_reduction' and datetime.now() <= self.validity_date and self.order_id.pending_amount - self.derate_amount == 0:
                    value = {
                        'pending_amount': self.order_id.pending_amount - self.derate_amount,
                    }
                    if self.order_id.pending_amount - self.derate_amount == 0:
                        value['repayment_success_date'] = datetime.now()
                        value['order_status_id'] = self.env['order.status'].search([('code', '=', '7')])  # 还款成功
                    self.order_id.sudo().write(value)
