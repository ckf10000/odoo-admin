# !user/bin/env python3
# -*- coding: utf-8 -*-
# Author: ChaoqiYin
import threading

import redis

from odoo import tools

CONFIG = tools.config.options


class RedisUtil(object):
    _instance_lock = threading.Lock()

    redis_host = CONFIG.get('redis_host', 'localhost')

    redis_port = CONFIG.get('redis_port', 6379)

    redis_password = CONFIG.get('redis_password', None)

    redis_pool = None

    def __init__(self):
        self._redis = redis.Redis(connection_pool=self.redis_pool)

    # 单例模式new
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            with RedisUtil._instance_lock:
                if not hasattr(cls, '_instance'):
                    cls._instance = super().__new__(cls)
                    cls._instance.redis_pool = cls.redis_pool = redis.ConnectionPool(
                        host=cls.redis_host, port=cls.redis_port, decode_responses=True,
                        password=cls.redis_password
                    )
        return cls._instance

    def _get_redis(self, db_number=0):
        return redis.Redis(connection_pool=self.redis_pool, db=db_number)

    @property
    def redis(self):
        if not hasattr(self, '_redis'):
            with RedisUtil._instance_lock:
                self._redis = self._get_redis()
        return self._redis

    def get_redis(self, db_number=0):
        return self._get_redis(db_number)
