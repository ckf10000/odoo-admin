# -*- encoding: utf-8 -*-

import logging
import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
import odoo
import odoo.modules.registry
from odoo.tools.translate import _
from odoo import http, tools
from odoo.http import content_disposition, request, Response
from odoo.addons.web.controllers.utils import ensure_db, _get_login_redirect_url
from ..utils import captcha

_logger = logging.getLogger(__name__)


class Home(http.Controller):

    def _login_redirect(self, uid, redirect=None):
        return _get_login_redirect_url(uid, redirect)
    
    # override
    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)

        if not request.uid:
            # request.uid = odoo.SUPERUSER_ID
            request.update_env(user=odoo.SUPERUSER_ID)

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            try:
                if values.get('captcha', "").lower().replace(" ", "") != request.session.get('login_captcha', 'odoo'):
                    raise odoo.exceptions.AccessDenied('Wrong Captcha')

                uid = request.session.authenticate(
                    request.session.db, 
                    request.params['login'],
                    request.params['password']
                )
                request.params['login_success'] = True
                return request.redirect(self._login_redirect(uid, redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Only employees can access this database. Please contact the administrator.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True
        
        response = request.render('loan_login.login_template', values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    @http.route('/loan_login/refresh_captcha', type='http', auth="none")
    def refresh_captcha(self, *args, **kw):
        # 加载验证码
        img_data, code = captcha.generate_captcha()
        request.session['login_captcha'] = code
        return http.Stream(type='data', data=img_data, mimetype='image/png').get_response()

class Website(Home):

    # override
    @http.route(website=True, auth="public", sitemap=False)
    def web_login(self, *args, **kw):
        return super().web_login(*args, **kw)