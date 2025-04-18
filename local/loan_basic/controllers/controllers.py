# -*- coding: utf-8 -*-
# from odoo import http


# class JhyBasic(http.Controller):
#     @http.route('/jhy_basic/jhy_basic', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/jhy_basic/jhy_basic/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('jhy_basic.listing', {
#             'root': '/jhy_basic/jhy_basic',
#             'objects': http.request.env['jhy_basic.jhy_basic'].search([]),
#         })

#     @http.route('/jhy_basic/jhy_basic/objects/<model("jhy_basic.jhy_basic"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('jhy_basic.object', {
#             'object': obj
#         })

