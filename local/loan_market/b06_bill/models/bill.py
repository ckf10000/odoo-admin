import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class BillStatus(models.Model):
    _name = 'bill.status'
    _description = '状态码'
    _rec_name = 'status_name'
    _order = 'sequence'
    _table = 'T_bill_status'

    enum_code = fields.Integer(string='枚举编码', required=True)
    status_name = fields.Char(string='状态名称', required=True)
    sequence = fields.Integer(string='排序', required=True)



class LoanBill(models.Model):
    _name = 'loan.bill'
    _description = 'bill'
    _inherit = ['loan.basic.model', 'bill.base.fields']
    _table = 'T_bill'

    matrix_id = fields.Many2one('joint.loan.matrix', string='共贷矩阵')
    product_id = fields.Many2one('loan.product', string='关联产品')
    product_name = fields.Char('产品名称')
    matrix_id = fields.Integer('共贷矩阵id')
    
    user_name = fields.Char('用户姓名')
    user_card_id = fields.Char('身份证号码')
    customer_type = fields.Integer('客户类型')
    system_type = fields.Integer('系统客户类型')
    group_id = fields.Integer('包(体系)编号')
    cross_type = fields.Integer('是否是互通用户')
    channel = fields.Char('流量渠道')
    market_channel = fields.Char('应用市场渠道')

    order_no = fields.Char('订单号')
    extension_bill_id = fields.Integer('展期订单id')
    reloan_flag = fields.Boolean('是否复贷')
    bill_status = fields.Integer('订单状态')
 
    account_id_1 = fields.Integer('放款账号id1')
    account_id_2 = fields.Integer('放款账号id2')
    account_id_3 = fields.Integer('放款账号id3')
    account_id_4 = fields.Integer('放款账号id4')
    account_id_5 = fields.Integer('放款账号id5')

    min_amount = fields.Float('最小金额')
    max_amount = fields.Float('最大金额')
    contract_amount = fields.Float('合同金额')
    loan_period = fields.Integer('还款周期')
    overdue_flag = fields.Boolean('是否逾期')
    deduct_type = fields.Integer('砍头息扣除类型')
    management_fee_rate = fields.Float('管理费费率')
    management_fee = fields.Float('管理费用')

    interest_amount = fields.Float('后置利息')
    interest_fee = fields.Float('利息')
    credit_fee = fields.Float('征信服务费')
    account_manage_fee = fields.Float('账号管理费')
    platform_service_fee = fields.Float('平台服务费')
    risk_fee = fields.Float('风险管理费')
    overdue_rate = fields.Float('逾期罚息日利率')
    late_fee = fields.Float('滞纳金')
    extension_rate = fields.Float('展期费率')
    extension_service_fee = fields.Float('展期服务费')
    apply_time = fields.Integer('申请时间')
    send_time = fields.Integer('推单时间')
    send_num = fields.Integer('发送次数')
    machine_success_time = fields.Integer('机审通过时间')
    audit_finish_time = fields.Integer('信审完成时间')
    last_time_send_out_money = fields.Integer('财务最后放款时间')
    loan_finish_time = fields.Integer('放款完成时间')

    refuse_code = fields.Integer('拒绝原因')
    refuse_time = fields.Integer('拒绝时间')
    refused_in_the_past_flag = fields.Boolean('是否曾经拒绝过')
    repay_completion_time = fields.Integer('还款完成时间')
    due_time = fields.Integer('到期时间')
    pending_amount = fields.Float('挂账金额')
    withdrawal_code = fields.Char('放款码')
    remark = fields.Char('备注')
    #芹文对接风控需要增加的字段
    interest_fee = fields.Float('利息费')
    risk_score = fields.Float('风控评分')
    risk_score_send_time = fields.Integer('风控评分发送时间')
    repayed_amount = fields.Float('已还金额')


    