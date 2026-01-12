# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

from odoo import models, fields


class ResCompany(models.Model):

    _inherit = 'res.company'

    muk_document_folder_id = fields.Char(string='Folder ID', requred=True)
