# -*- coding: utf-8 -*-
import base64
import xlrd
from datetime import datetime
from xlrd import xldate_as_tuple

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class CollectionStageSettingWizard(models.TransientModel):
    _name = 'collection.stage.setting.wizard'
    _table = "C_stage_setting_wizard"  
    _description = '催收阶段配置向导'



    def action_confirm(self):
        """
        确认按钮
        """
        self.env['collection.stage.setting'].browse(self._context.get('active_ids')).unlink()

