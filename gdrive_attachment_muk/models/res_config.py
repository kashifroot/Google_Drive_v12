# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    muk_document_folder_id = fields.Char(related='company_id.muk_document_folder_id', readonly=False, string="Muk Folder ID",
                                         help="make a folder on drive in which you want to upload files; then open that folder; the last thing in present url will be folder id")
