from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo import exceptions
from odoo.tools import float_round
import logging


_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError


