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

from odoo import models, fields, api
import json
from datetime import datetime
import functools
import operator
from googleapiclient.http import HttpError

class File(models.Model):

    _inherit = 'muk_dms.file'

    file_id = fields.Char()
    file_url = fields.Char(default='')
    upload_mail = fields.Boolean(string="Send Mail?")
    content = fields.Binary(compute='_compute_content', inverse='_inverse_content', string='Content', attachment=False, prefetch=False, store=False)
    so_document_ids = fields.One2many('sale.order.document', 'file_id', string="Document Detail")
    internal = fields.Boolean(string="Internal")
    valid_from = fields.Date(string="Valid From")
    valid_to = fields.Date(string="Valid To")
    is_expired = fields.Boolean(string="Is Expired", compute="is_document_expired", store=True)

    @api.depends('valid_to', 'internal')
    def is_document_expired(self):
        for res in self:
            # print ("asdfasdfasdf", res.valid_to <= datetime.today().date())
            # if res.valid_to and res.internal and res.valid_to >= datetime.today().date():
            if res.internal or res.valid_to and res.valid_to < datetime.today().date():
                res.is_expired = True
                res.upload_mail = False
            else:
                res.is_expired = False

    @api.model
    def create(self, vals):
        res = super(File, self).create(vals)
        self.env.user.company_id.check_token_expirey()
        if res and res.directory:
            parent_id = res.directory.folder_id
            if not parent_id:
                parent_id = res.directory.create_folder_on_google_drive(res.directory.name, res.directory._name)
            drive_file_obj = self.env['ir.attachment'].upload_file_on_drive(res.name, res.content, parent_id)
            if drive_file_obj:
                res.write({
                    'file_id': drive_file_obj.get('id'),
                    'file_url': drive_file_obj.get('download_link'),
                })
        return res

    @api.multi
    def write(self, value):
        self.env.user.company_id.check_token_expirey()
        Attachment = self.env['ir.attachment']
        if 'content' in value and self.file_id:
            try:
                Attachment.delete_file_from_drive(self.file_id)
            except HttpError:
                pass
            parent_id = value.get('directory') and self.directory.browse(value.get('directory'))
            if not parent_id:
                parent_id = self.directory.folder_id
            res = super(File, self).write(value)
            drive_file_obj = self.env['ir.attachment'].upload_file_on_drive(self.name, self.content, parent_id)
            if drive_file_obj:
                self.write({
                    'file_id': drive_file_obj.get('id'),
                    'file_url': drive_file_obj.get('download_link'),
                })
            return res
        return super(File, self).write(value)

    @api.multi
    def unlink(self):
        self.env.user.company_id.check_token_expirey()
        for rec in self:
            if rec.file_id:
                Attachment = rec.env['ir.attachment']
                try:
                    Attachment.delete_file_from_drive(rec.file_id)
                except HttpError:
                    pass
        return super(File, self).unlink()

    @api.multi
    def cron_upload_attachments(self):
        company_id = self.env.user.company_id
        attachment_ids = self.env['muk_dms.file'].search([('file_id', '=', False), ('company', '=', company_id.id)], limit=10)
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
    def send_mail_for_document(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('gdrive_attachment_muk', 'muk_document_mail_template')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'muk_dms.file',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'mass_mail'
        })

        if self.content:
            attachment = {
                'name': ("%s" % self.name),
                'datas': self.content,
                'datas_fname': self.name,
                'res_model': 'muk_dms.file',
                'type': 'binary'
            }
            att_id = self.env['ir.attachment'].create(attachment)
            ctx.update({'default_attachment_ids':  [(4, att_id.id)]})
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

    @api.depends('name', 'directory', 'directory.parent_path')
    def _compute_path(self):
        records_with_directory = self - self.filtered(lambda rec: not rec.directory)
        if records_with_directory and records_with_directory.ids:
            print("rec.directory.parent_path", records_with_directory)
            paths = [list(map(int, rec.directory.parent_path.split('/')[:-1])) for rec in records_with_directory]
            model = self.env['muk_dms.directory'].with_context(dms_directory_show_path=False)
            directories = model.browse(set(functools.reduce(operator.concat, paths)))
            data = dict(directories._filter_access('read').name_get())
            for record in self:
                path_names = []
                path_json = []
                for id in reversed(list(map(int, record.directory.parent_path.split('/')[:-1]))):
                    if id not in data:
                        break
                    path_names.append(data[id])
                    path_json.append({
                        'model': model._name,
                        'name': data[id],
                        'id': id,
                    })
                path_names.reverse()
                path_json.reverse()
                name = record.name_get()
                path_names.append(name[0][1])
                path_json.append({
                    'model': record._name,
                    'name': name[0][1],
                    'id': isinstance(record.id, int) and record.id or 0,
                })
                record.update({
                    'path_names': '/'.join(path_names),
                    'path_json': json.dumps(path_json),
                })


class SaleOrderDocument(models.Model):
    _name = 'sale.order.document'
    _description = 'Sale Order Document Send'

    file_id = fields.Many2one('muk_dms.file')
    partner_id = fields.Many2one('res.partner', string="Customer")
    send_datetime = fields.Datetime(string="Send Date")
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
