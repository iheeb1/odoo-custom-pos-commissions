# -*- coding: utf-8 -*-

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_commission_enabled = fields.Boolean(
        related="pos_config_id.commission_enabled", readonly=False
    )

    pos_commission_journal_id = fields.Many2one(
        related="pos_config_id.commission_journal_id", readonly=False
    )

    pos_commission_expense_account_id = fields.Many2one(
        related="pos_config_id.commission_expense_account_id", readonly=False
    )

    pos_commission_liability_account_id = fields.Many2one(
        related="pos_config_id.commission_liability_account_id", readonly=False
    )

    pos_commission_calc_base = fields.Selection(
        related="pos_config_id.commission_calc_base", readonly=False
    )

    pos_default_commission_rule_id = fields.Many2one(
        related="pos_config_id.default_commission_rule_id", readonly=False
    )
