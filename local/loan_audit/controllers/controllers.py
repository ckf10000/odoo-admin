# -*- coding: utf-8 -*-
# from odoo import http


# class Cas(http.Controller):
#     @http.route('/cas/cas', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cas/cas/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('cas.listing', {
#             'root': '/cas/cas',
#             'objects': http.request.env['cas.cas'].search([]),
#         })

#     @http.route('/cas/cas/objects/<model("cas.cas"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cas.object', {
#             'object': obj
#         })

