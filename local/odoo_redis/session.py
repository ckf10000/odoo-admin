from odoo.tools._vendor.sessions import SessionStore
from odoo.service import security
from odoo.tools.func import lazy_property
from odoo import http, tools
from odoo.http import request
import redis
import json
import logging

_logger = logging.getLogger(__name__)

SESSION_LIFETIME = 60 * 60 * 24 * 7

CONFIG = tools.config.options


class RedisSessionStore(SessionStore):

    def __init__(self, session_class=None):
        SessionStore.__init__(self, session_class)
        # 设置存储session的key的前缀
        self.prefix = tools.config.get('redis_session_key_prefix', 'erp_session_')
        # 设置session的有效期时长（秒），默认为一周
        self.session_lifetime = int(tools.config.get('redis_session_lifetime', SESSION_LIFETIME))
        self.pool = redis.ConnectionPool(
            host=tools.config.get('redis_host', '127.0.0.1'),  # redis IP地址
            port=tools.config.get('redis_port', 6379),  # redis 端口号
            db=tools.config.get('redis_db', 0),  # redis数据库
            password=tools.config.get('redis_password', None),  # redis数据库密码
            max_connections=int(tools.config.get('redis_max_conn', 0))  # redis 连接池最大连接数
        )
        self.conn = redis.Redis(connection_pool=self.pool)

    def _encode_session_key(self, key):
        ''' 将session的key转换为utf-8编码'''

        return key.encode("utf-8") if isinstance(key, str) else key

    def _get_session_key(self, sid):
        ''' 拼接session的key的前缀'''

        return self._encode_session_key(self.prefix + sid)

    def save(self, session):
        ''' 用于将session保存到redis中，并设置过期时间'''

        key = self._get_session_key(session.sid)
        self.conn.setex(name=key, value=json.dumps(dict(session)), time=self.session_lifetime)

    def delete(self, session):
        ''' 用于用户退出登录时，删除redis中的session'''

        key = self._get_session_key(session.sid)
        self.conn.delete(key)

    def get(self, sid):
        ''' 用于系统对session的获取。'''

        if not self.is_valid_key(sid):
            return self.new()
        else:
            try:
                key = self._get_session_key(sid)
                data = json.loads(self.conn.get(key))
                if data:
                    # 刷新session的有效期时长
                    self.conn.expire(key, self.session_lifetime)
            except Exception:
                _logger.debug('Could not load session data. Use empty session.', exc_info=True)
                data = {}

            return self.session_class(data, sid, False)

    def list(self):
        ''' 用于获取session列表，该方法对redis系统资源消耗太大，未实现。'''
        _logger.warning("This method is not yet implemented!")
        raise NotImplementedError('Not implemented')

    def rotate(self, session, env):
        ''' 用户session重新生成，类似刷新session的功能，直接从源码复制过来的，未做修改。'''

        self.delete(session)
        session.sid = self.generate_key()
        if session.uid and env:
            session.session_token = security.compute_session_token(session, env)
        session.should_rotate = False
        self.save(session)


    def vacuum(self, max_lifetime=SESSION_LIFETIME):
        ''' 用于清理过期的session信息，由于使用redis存储session，session自带过期时间，所以该方法不用实现'''
        _logger.debug('Redis automatically clears expired sessions，Function not implemented!')


class ExtendApplication(http.Application):
    ''' 继承http.Application，重写session_store方法，在session方法中做判断，选择使用哪一种session存储方案'''

    @lazy_property
    def session_store(self):
        # 当配置文件中配置了session_store_redis则使用redis存储session，否则还是使用原生的文件存储session。
        if tools.config.get("session_store_redis"):
            # _logger.info('HTTP sessions stored in Redis')
            return RedisSessionStore(session_class=http.Session)

        return super(ExtendApplication, self).session_store


# 实例化ExtendApplication类覆盖原Application类的对象
http.root = ExtendApplication()