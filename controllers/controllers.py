# -*- coding: utf-8 -*-
# from odoo import http


# class ReportsDesign(http.Controller):
#     @http.route('/reports_design/reports_design', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/reports_design/reports_design/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('reports_design.listing', {
#             'root': '/reports_design/reports_design',
#             'objects': http.request.env['reports_design.reports_design'].search([]),
#         })

#     @http.route('/reports_design/reports_design/objects/<model("reports_design.reports_design"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('reports_design.object', {
#             'object': obj
#         })

