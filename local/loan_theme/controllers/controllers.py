# -*- coding: utf-8 -*-
# from odoo import http


# class WebsiteAirproof(http.Controller):
#     @http.route('/website_airproof/website_airproof', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/website_airproof/website_airproof/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('website_airproof.listing', {
#             'root': '/website_airproof/website_airproof',
#             'objects': http.request.env['website_airproof.website_airproof'].search([]),
#         })

#     @http.route('/website_airproof/website_airproof/objects/<model("website_airproof.website_airproof"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('website_airproof.object', {
#             'object': obj
#         })

