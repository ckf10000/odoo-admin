# -*- coding: utf-8 -*-
""""
学习平台 REST API

接口前缀: /api/v1/learn/

认证方式: 统一请求格式 POST + api_verify_auth

响应格式:
  {
    "success": true/false,
    "data": {...},
    "message": "...",
    "error": "..."  // 仅在失败时
  }
"""
from . import common
from . import nav
from . import process
from . import content
from . import exam
from . import interact
from . import group
