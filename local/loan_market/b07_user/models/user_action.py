import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class UserActionPhase(models.Model):
    _name = 'user.action.phase'
    _description = 'User Actopn Phase'
    _table = 'T_phase_of_user_action'
    _rec_name = 'phase_name'
    _order = 'sequence'

    enum_code = fields.Integer(string='枚举编号')
    phase_name = fields.Char(string='阶段名称')
    sequence = fields.Integer(string='序号')


# class UserAction(models.Model):
#     _name = 'user.action'
#     _description = 'UserActopn'
#     _inherit = ['loan.basic.model', 'loan.base.fields']
#     _table = 'T_user_action'

#     app_id = fields.Many2one('loan.app', string='App')
#     user_id = fields.Many2one('res.users', string='用户')
#     phone_no = fields.Char(string='手机号')
#     equip_id = fields.Char(string='设备Id')
#     encrypt_version = fields.Char(string='加密版本')
#     action_code = fields.Integer(string='操作码')
#     action_time = fields.Integer(string='操作时间')
#     action_success_flag = fields.Boolean(string='操作是否成功', default=True)


class UserActionLogin(models.Model):
    _name = 'user.action.login'
    _description = 'UserActopn'
    _inherit = ['loan.basic.model', 'loan.base.fields']
    _table = 'T_user_action_login'

    login_time = fields.Integer(string='登录时间')


class UserActionSendVCode(models.Model):
    _name = 'user.action.send.v.code'
    _description = 'UserActionSendVCode'
    _inherit = ['loan.basic.model', 'loan.base.fields']
    _table = 'T_user_action_send_v_code'

    send_req_time = fields.Integer(string='发送请求时间')
    send_notify_time = fields.Integer(string='发送通知时间')
    send_result_code = fields.Integer(string='发送结果代码')


class UserActionLivingRec(models.Model):
    _name = 'user.action.living.rec'
    _description = 'UserActionLivingRec'
    _inherit = ['loan.basic.model', 'loan.base.fields']
    _table = 'T_user_action_living_rec'

    rec_time = fields.Integer()
    result_code = fields.Integer()
    result = fields.Json()
    snapshot_upload_success_flag = fields.Boolean(string='snapshot upload success flag')
    snapshot_url = fields.Char(string='snapshot url')
    phase_code = fields.Integer(string="识别阶段")


class UserActionMatch121(models.Model):
    _name = 'user.action.match.121'
    _description = '1:1匹配'
    _inherit = ['loan.basic.model', 'loan.base.fields']
    _table = 'T_user_action_match_121'

    match_time = fields.Integer(string='匹配时间')
    result_code = fields.Integer(string='1:1匹配结果')
    result = fields.Json()
    phase_code = fields.Integer(string='1:1识别阶段')


class UserActionOcr(models.Model):
    _name = 'user.action.ocr'
    _description = 'ocr 识别'
    _inherit = ['loan.basic.model', 'loan.base.fields']
    _table = 'T_user_action_ocr'

    ocr_time = fields.Integer(string='ocr识别时间')
    result_code = fields.Integer(string='ocr识别结果')
    result = fields.Json()
    phase_code = fields.Integer(string='ocr识别阶段')