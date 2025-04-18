import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class UserIdentity(models.Model):
    """
     class T_identity {
        id: int, key, ODOO standard
        app_id: int, not null, key of T_app. part of composite key
        user_id: int, not null, key of T_user. part of composite key

        gender_code: int, not null, see EnumCode_gender_*
        birth_date: long, not null
        education_code: int, not null, see EnumCode_education_*
        marital_status_code: int, not null, see EnumCode_marital_status_*
        housing_status_code: int, not null, see EnumCode_housing_status_*
        children_num_code: int, not null, see EnumCode_children_num_*
        loan_purpose_code: int, not null, see EnumCode_loan_purpose_*
        occupation_code: int, not null, see EnumCode_occupation_*
        salary_code: int, not null, see EnumCode_salary_*
        pay_day_code: int, not null, see EnumCode_pay_day_*

        finished_flag: bool, not null, False initially
    }
    """
    _name = 'user.identity'
    _description = '用户身份信息'
    _inherit = ['loan.basic.model']
    _table = 'T_identity'

    user_id = fields.Many2one('loan.user', string='User', required=True)
    app_id = fields.Many2one('loan.app', string='App', related='user_id.app_id', store=True)
    gender_code = fields.Integer(string='性别')
    birth_date = fields.Integer(string='生日')
    occupation_code = fields.Integer(string='职业')
    education_code = fields.Integer(string='学历')
    marital_status_code = fields.Integer(string='婚姻状况')
    salary_code = fields.Integer(string='月收入')
    housing_status_code = fields.Integer(string='居住状况')
    children_num_code = fields.Integer(string='子女数量')
    loan_purpose_code = fields.Integer(string='贷款用途')
    pay_day_code = fields.Integer(string='发薪日')
    finished_flag = fields.Boolean(string='是否完成通讯录填写')


class UserContact(models.Model):
    """
    class T_contact {
        id: int, key, ODOO standard
        app_id: int, not null, key of T_app. part of composite key
        user_id: int, not null, key of T_user. part of composite key

        contact_type_code_1: int, not null, see EnumCode_contact_type_*
            // EnumCode_contact_type_primary
            // EnumCode_contact_type_secondary
            // EnumCode_contact_type_other
        relation_code_1: int, not null, see EnumCode_relation_*
        phone_no_1: str, not null

        contact_type_code_2: int, not null, see EnumCode_contact_type_*
        relation_code_2: int, not null, see EnumCode_relation_*
        phone_no_2: str, not null

        contact_type_code_3: int, not null, see EnumCode_contact_type_*
        relation_code_3: int, not null, see EnumCode_relation_*
        phone_no_3: str, not null

        encrypt_version: str, maybe null

        finished_flag: bool, not null, False initially
    }
    """
    _name = 'user.contact'
    _description = '用户联系人信息'
    _inherit = ['loan.basic.model']
    _table = 'T_contact'

    user_id = fields.Many2one('loan.user', string='User', required=True)
    app_id = fields.Many2one('loan.app', string='App', related='user_id.app_id', store=True)

    contact_type_code_1 = fields.Integer(string='联系人类型1')
    relation_code_1 = fields.Integer(string='关系1')
    phone_no_1 = fields.Char(string='电话1')
    name_1 = fields.Char(string="姓名1")
    update_time_1 = fields.Integer(string="联系人修改时间1")

    contact_type_code_2 = fields.Integer(string='联系人类型2')
    relation_code_2 = fields.Integer(string='关系2')
    phone_no_2 = fields.Char(string='电话2')
    name_2 = fields.Char(string="姓名2")
    update_time_2 = fields.Integer(string="联系人修改时间2")

    contact_type_code_3 = fields.Integer(string='联系人类型3')
    relation_code_3 = fields.Integer(string='关系3')
    phone_no_3 = fields.Char(string='电话3')
    name_3 = fields.Char(string="姓名3")
    update_time_3 = fields.Integer(string="联系人修改时间3")
    
    encrypt_version = fields.Char(string='加密版本')
    finished_flag = fields.Boolean(string='是否完成联系人填写')


class IdPhotoSet(models.Model):
    """
    class T_id_photo_set {
        id: int, key, ODOO standard
        app_id: int, not null, key of T_app
        user_id: int, not null

        photo_code_1: int, maybe null, see EnumCode_id_photo_*
            // EnumCode_id_photo_pan_card_front
            // EnumCode_id_photo_pan_card_back
            // EnumCode_id_photo_id_card_front
            // EnumCode_id_photo_id_card_hold
        photo_url_1: str, maybe null, URL of photo_1, maybe null

        photo_code_2: int, maybe null, see EnumCode_id_photo_*
        photo_url_2: str, maybe null, URL of photo_2, maybe null

        photo_code_3: int, maybe null, see EnumCode_id_photo_*
        photo_url_3: str, maybe null, URL of photo_3, maybe null

        photo_code_4: int, maybe null, see EnumCode_id_photo_*
        photo_url_4: str, maybe null, URL of photo_4, maybe null

        ocr_title_code_1: int, maybe null, see EnumCode_ocr_title_*
            // EnumCode_ocr_title_pan_name
            // EnumCode_ocr_title_pan_number
        ocr_result_1: str, maybe null
        ocr_changed_1: bool, maybe null
        ocr_text_1: str, maybe null
        // when ocr_changed_1 = false, ocr_text_1 will also be null, which means
        // ocr_result_1 was not touched

        ocr_title_code_2: int, maybe null, see EnumCode_ocr_title_*
        ocr_result_2: str, maybe null
        ocr_changed_2: bool, maybe null
        ocr_text_2: str, maybe null
        // when ocr_changed_2 = false, ocr_text_2 will also be null, which means
        // ocr_result_2 was not touched

        finished_flag: bool, not null
    }
    """
    _name = 'user.photo.set'
    _description = '用户证件照'
    _inherit = ['loan.basic.model']
    _table = 'T_id_photo_set'

    app_id = fields.Many2one('loan.app', string='APP配置copy', required=True)
    user_id = fields.Many2one('loan.user', string='关联用户', required=True)

    photo_code_1 = fields.Integer(string='照片1类型')
    photo_url_1 = fields.Char(string='照片1URL')

    photo_code_2 = fields.Integer(string='照片2类型')
    photo_url_2 = fields.Char(string='照片2URL')

    photo_code_3 = fields.Integer(string='照片3类型')
    photo_url_3 = fields.Char(string='照片3URL')

    photo_code_4 = fields.Integer(string='照片4类型')
    photo_url_4 = fields.Char(string='照片4URL')

    ocr_title_code_1 = fields.Integer(string='OCR标题1')
    ocr_result_1 = fields.Char(string='OCR结果1')
    ocr_changed_1 = fields.Boolean(string='OCR是否修改1')
    ocr_text_1 = fields.Char(string='OCR文本1')

    ocr_title_code_2 = fields.Integer(string='OCR标题2')
    ocr_result_2 = fields.Char(string='OCR结果2')
    ocr_changed_2 = fields.Boolean(string='OCR是否修改2')
    ocr_text_2 = fields.Char(string='OCR文本2')

    ocr_title_code_3 = fields.Integer(string="OCR标题3")
    ocr_result_3 = fields.Char(string="OCR结果3")
    ocr_changed_3 = fields.Boolean(string="OCR是否修改3")
    ocr_text_3 = fields.Char(string="OCR文本3")

    ocr_title_code_4 = fields.Integer(string="OCR标题4")
    ocr_result_4 = fields.Char(string="OCR结果4")
    ocr_changed_4 = fields.Boolean(string="OCR是否修改4")
    ocr_text_4 = fields.Char(string="OCR文本4")

    finished_flag = fields.Boolean(string='是否完成', default=False)
    


    
