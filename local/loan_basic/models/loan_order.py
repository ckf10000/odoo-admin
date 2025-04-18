import logging
from odoo import models, fields, api
from . import enums
from ..utils import LoanAPI


_logger = logging.getLogger(__name__)


class LoanOrder(models.Model):
    _name = 'loan.order'
    _description = '财务订单'
    _inherit = ['loan.basic.model']
    _table = 'F_loan_order'

    # 用户
    loan_user_id = fields.Many2one('loan.user', string='用户', auto_join=True, index=True)
    loan_uid = fields.Integer('UserID', related='loan_user_id.id')
    loan_user_name = fields.Char(string='姓名')
    loan_user_phone = fields.Char(string='手机号码', related="loan_user_id.phone_no")
    loan_user_unrepay_order_count = fields.Integer(string='待还订单数', related="loan_user_id.unrepay_order_count")

    # 订单
    bill_id = fields.Integer(string='账单')
    matrix_id = fields.Integer(string='矩阵')
    app_id = fields.Many2one('loan.app', string='APP')
    app_version = fields.Char(string='APP版本') # 下单时app版本
    
    product_id = fields.Many2one('loan.product', string='产品名称', required=True, auto_join=True, index=True)

    order_no = fields.Char(string='订单编号', required=True, index=True)
    order_type = fields.Selection(selection=enums.ORDER_TYPE, string='订单类型')
    apply_time = fields.Datetime('申请时间')
    contract_amount = fields.Float(string='合同金额', digits=(16, 2))
    loan_period = fields.Integer(string='借款期限')
    management_fee_rate = fields.Float('管理费费率')
    management_fee = fields.Float('管理费用', digits=(16, 2))
    loan_amount = fields.Float('放款金额', digits=(16, 2))
    bank_name = fields.Char(string='收款银行')
    bank_account_no = fields.Char(string='收款账号')
    bank_ifsc_code = fields.Char(string='收款银行联行号')
    
    # # 信审审核
    # audit_assign_status = fields.Selection(selection=enums.AUDIT_ASSIGN_STATUS, default='0', string='信审分配状态', index=True)
    # audit_assign_time = fields.Datetime(string='信审分配时间')
    # audit_user_id = fields.Many2one('res.users', string='信审员')
    # audit_status = fields.Selection(selection=enums.AUDIT_STATUS, default='0', string='信审结论')
    # audit_reason = fields.Selection(selection=enums.AUDIT_REASON, default='1', string='信审原因')
    # audit_remark = fields.Text(string='信审备注')
    # audit_time = fields.Datetime(string='信审时间')

    # 订单状态相关
    order_status = fields.Selection(selection=enums.ORDER_STATUS, string='订单状态', index=True)
    refuse_reason = fields.Text(string='拒绝原因')
    refuse_time = fields.Datetime(string='拒绝时间')

    def _get_api_svc(self):
        api_base_url = self.env['ir.config_parameter'].get_param('loan_api.base.url', '')
        api_svc = LoanAPI(api_base_url)
        return api_svc

    def create_bill_order(self, data):
        """
        创建账单订单
        """
        api_svc = self._get_api_svc()
        try:
            bill_id = api_svc.create_bill(data)
            return bill_id
        except Exception as e:
            _logger.error('接口创建账单订单失败: %s', e)
            return False

    def update_bill_order(self, data):
        """
        更新账单订单
        """
        api_svc = self._get_api_svc()
        try:
            data['id'] = self.bill_id
            api_svc.update_bill(data)
            return True
        except Exception as e:
            _logger.error('接口更新账单订单失败: %s', e)
            return False

    def update_user_profile(self, data):
        api_svc = self._get_api_svc()
        try:
            data['user_id'] = self.loan_uid
            api_svc.update_user_profile(data)
            return True
        except Exception as e:
            _logger.error('接口更新账单订单失败: %s', e)
            return False


    

    