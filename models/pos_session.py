# -*- coding: utf-8 -*-

from odoo import models, fields


class PosSession(models.Model):
    _inherit = "pos.session"

    def _load_pos_data_models(self, config):
        result = super(PosSession, self)._load_pos_data_models(config)
        return result
