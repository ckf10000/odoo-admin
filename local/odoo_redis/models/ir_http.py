import werkzeug

from odoo import models
from odoo.http import request
from .exception import RateLimitException
from .redis_util import RedisUtil


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    utils = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 216000
    }

    @classmethod
    def _convert_to_seconds(cls, rate):
        value, util = rate.split('/')
        if not str.isdigit(value):
            raise ValueError('频率值只能是数字')
        if util not in cls.utils.keys():
            raise ValueError('频率单位只能是%s' % ','.join(cls.utils.keys()))
        value = int(value)
        if value <= 0:
            raise ValueError('频率值必须 >=0 ')
        return [value, cls.utils[util]]

    @classmethod
    def _get_user_key(cls):
        return request.env.user.di

    @classmethod
    def _get_real_limit_key(cls, key):
        if callable(key):
            return key(request)
        if key not in ['ip', 'ip_or_user']:
            raise ValueError('频率限制Key类型只能是 ip 或者 ip_or_user')
        ip = request.httprequest.remote_addr
        if not request.env.user:
            return ip
        if key == 'ip':
            return ip
        else:
            return request.env.user.id

    @classmethod
    def _get_handler_rule(cls):
        if hasattr(request, 'handler_rule'):
            return request.handler_rule
        request.handler_rule = cls._find_handler(return_rule=True)
        return request.handler_rule

    @classmethod
    def _get_rate_limit_key(cls):
        if hasattr(request, 'rate_limit_key'):
            return request.rate_limit_key
        rule, _ = cls._get_handler_rule()
        func = rule.endpoint
        url_rule = rule.rule
        kw = func.routing
        request.rate_limit_key = '%s:%s' % (url_rule, cls._get_real_limit_key(kw.get('key', 'ip')))
        return request.rate_limit_key

    @classmethod
    def _get_request_time(cls):
        key = cls._get_rate_limit_key()
        redis = request.redis
        if request.redis.exists(key):
            return int(redis.get(key))
        else:
            return 0

    @classmethod
    def _get_limit_rate(cls):
        rule, _ = cls._get_handler_rule()
        kw = rule.endpoint.routing
        if 'rate' in kw:
            return kw['rate']
        else:
            return False

    @classmethod
    def _update_request_time(cls):
        try:
            rate = cls._get_limit_rate()
            if not rate:
                return False
            _, seconds = cls._convert_to_seconds(rate)
            request_time = cls._get_request_time()
            key = cls._get_rate_limit_key()
            if request_time == 0:
                request.redis.set(key, 1, ex=seconds)
            else:
                expire_seconds = request.redis.get(key) or seconds
                request.redis.set(key, request_time + 1, ex=expire_seconds)
        except Exception as e:
            if isinstance(e, werkzeug.exceptions.HTTPException) and e.code == 404:
                return True
            else:
                raise e

    @classmethod
    def _check_real_limit(cls):
        try:
            rate = cls._get_limit_rate()
            if not rate:
                return False
            count, seconds = cls._convert_to_seconds(rate)
            request_time = cls._get_request_time()
            if request_time >= count:
                raise RateLimitException('操作请求过于频繁，请稍后再试', count - request_time)
        except Exception as e:
            if isinstance(e, werkzeug.exceptions.HTTPException) and e.code == 404:
                return True
            else:
                raise e

    @classmethod
    def _dispatch(cls, endpoint):
        request.redis = RedisUtil().redis
        try:
            cls._get_handler_rule()
        except Exception as e:
            if isinstance(e, werkzeug.exceptions.HTTPException) and e.code == 404:
                return super(IrHttp, cls)._dispatch(endpoint)
            else:
                raise e
        try:
            cls._check_real_limit()
        except RateLimitException as e:
            return werkzeug.wrappers.Response(e.args[0], status=433)
        request.request_time = cls._get_request_time()
        response = super(IrHttp, cls)._dispatch(endpoint)
        cls._update_request_time()
        return response
