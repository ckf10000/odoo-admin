# -*- coding: utf-8 -*-
# from odoo import http


# class LoanCss(http.Controller):
#     @http.route('/loan_css/loan_css', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/loan_css/loan_css/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('loan_css.listing', {
#             'root': '/loan_css/loan_css',
#             'objects': http.request.env['loan_css.loan_css'].search([]),
#         })

#     @http.route('/loan_css/loan_css/objects/<model("loan_css.loan_css"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('loan_css.object', {
#             'object': obj
#         })

