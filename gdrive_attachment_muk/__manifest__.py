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

{
    'name': 'Muk Google Drive Attachment',
    'version': '12.0.2',
    "author": "Excelroot Technology Sdn Bhd",
    "website": "https://www.excelroot.com/",
    'license': 'AGPL-3',
    'Summary': 'Tailoring',
    'description': 'This module is for upload muk documents on google drive. ',
    'sequence': '2',
    'depends': ['muk_dms', 'google_drive', 'sale', 'google_drive_attachment'],
    'data': [
        'security/ir.model.access.csv',
        'data/upload_cron_job.xml',
        'data/attachment_muk.xml',
        'views/res_config_view.xml',
        'views/muk_file_view.xml',
        'views/muk_dir_view.xml',
    ],
    'installable': True,
    'application': True,
}
