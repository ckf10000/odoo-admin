# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
import requests

_logger = logging.getLogger(__name__)


class APICaller(models.Model):
    _name = "api.caller"
    _description = "API Caller"

    def call_risktask_api(self):
        # 检查系统参数中是否设置了API URL
        risk_task_url = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("risk_task_url", default="False")
        )

        if risk_task_url:
            # url = "http://172.16.7.24:18000/billInter/riskTask"
            try:
                response = requests.post(risk_task_url)
                if response.status_code == 200:
                    # 成功调用API
                    _logger.info(
                        "API called successfully, response: %s", response.json()
                    )
                else:
                    _logger.error(
                        "Failed to call API, status code: %s", response.status_code
                    )
            except Exception as e:
                _logger.error("Error calling API: %s", e)
        else:
            _logger.info("risk_task_url is not set")

    def call_hzrisktask_api(self):
        # 检查系统参数中是否设置了API URL
        risk_task_url = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("hz_risk_task_url", default="False")
        )

        if risk_task_url:
            # url = "http://172.16.7.24:18000/billInter/hZRiskTask"
            try:
                response = requests.post(risk_task_url)
                if response.status_code == 200:
                    # 成功调用API
                    _logger.info(
                        "HZ Risk Task API called successfully, response: %s",
                        response.json(),
                    )
                else:
                    _logger.error(
                        "Failed to call HZ Risk Task API, status code: %s",
                        response.status_code,
                    )
            except Exception as e:
                _logger.error("Error calling HZ Risk Task API: %s", e)
        else:
            _logger.info("hz_risk_task_url is not set")

    def call_riskscoretask_api(self):
        # 检查系统参数中是否设置了API URL
        risk_task_url = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("risk_score_task_url", default="False")
        )

        if risk_task_url:
            # url = "http://172.16.7.24:18000/billInter/riskScoreTask"
            try:
                response = requests.post(risk_task_url)
                if response.status_code == 200:
                    # 成功调用API
                    _logger.info(
                        "Risk Score Task API called successfully, response: %s",
                        response.json(),
                    )
                else:
                    _logger.error(
                        "Failed to call Risk Score Task API, status code: %s",
                        response.status_code,
                    )
            except Exception as e:
                _logger.error("Error calling Risk Score Task API: %s", e)
        else:
            _logger.info("risk_score_task_url is not set")
