# -*- encoding: UTF-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015-Today Laxicon Solution.
#    (<http://laxicon.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from odoo import models, fields, api, _
from odoo.addons.google_drive.models.google_drive import GoogleDrive
import json
import requests


class Directory(models.Model):

    _inherit = 'muk_dms.directory'

    folder_id = fields.Char()

    @api.multi
    def create_folder_on_google_drive(self, folder_name, model_obj=None):
        parent_folder = self.env.user.company_id.muk_document_folder_id
        if self._context.get('parent_path', False):
            parent_folder = self._context.get('parent_path', False)
        if parent_folder:
            return self.env['ir.attachment'].create_folder_on_drive(folder_name, parent_folder)

    @api.model
    def create(self, vals):
        self.env.user.company_id.check_token_expirey()
        res = super(Directory, self).create(vals)
        if res.parent_directory:
            parent_id = self.with_context(parent_path=res.parent_directory.folder_id).create_folder_on_google_drive(res.name, res._name)
        else:
            parent_id = self.create_folder_on_google_drive(res.name, res._name)
        res.folder_id = parent_id
        return res

    @api.multi
    def cron_upload_attachments(self):
        company_id = self.env.user.company_id
        attachment_ids = self.env['muk_dms.directory'].search([('folder_id', '=', False), ('company', '=', company_id.id)], limit=10)
        for res in attachment_ids:
            parent_id = res.directory.folder_id
            if not parent_id:
                parent_id = res.directory.create_folder_on_google_drive(res.name, res._name)
            file_url = self.env['file.upload'].upload_to_google_drive(res.name, res.content, parent_id)
            if file_url:
                # res.content = False
                res.file_id = file_url.get('file_id')
                res.file_url = file_url.get('url')

    @api.multi
    def send_mail_for_directory(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('gdrive_attachment_muk', 'muk_directory_mail_template')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'muk_dms.directory',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'mass_mail',
            'default_email_from': self.env.user.email_formatted,
            'default_partner_ids': [(6, 0, self.env.user.partner_id.ids)],

        })

        if self.files:
            lst = []
            for file in self.files:
                if not file.is_expired and file.upload_mail:
                    attachment = {
                        'name': ("%s" % file.name),
                        'datas': file.content,
                        'datas_fname': file.name,
                        'res_model': 'muk_dms.directory',
                        'type': 'binary'
                    }
                    att_id = self.env['ir.attachment'].create(attachment)
                    lst.append(att_id.id)
            ctx.update({'default_attachment_ids':  [(6, 0, lst)]})
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
