# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = "pos.config"

    commission_enabled = fields.Boolean(string="Enable Commissions", default=False)

    commission_journal_id = fields.Many2one(
        "account.journal",
        string="Commission Journal",
        domain=[("type", "=", "general")],
        help="Journal used to post commission entries.",
    )

    commission_expense_account_id = fields.Many2one(
        "account.account",
        string="Commission Expense Account",
        domain=[("account_type", "=", "expense")],
        help="Account to debit for commission expenses.",
    )

    commission_liability_account_id = fields.Many2one(
        "account.account",
        string="Commission Liability Account",
        domain=[("account_type", "=", "liability_current")],
        help="Account to credit for commission liabilities (payable to employees).",
    )

    commission_calc_base = fields.Selection(
        [
            ("after_discount", "After Discount"),
            ("before_discount", "Before Discount"),
        ],
        string="Commission Calculation Base",
        default="after_discount",
        help="Calculate commission on price before or after discount.",
    )

    default_commission_rule_id = fields.Many2one(
        "pos.commission.rule",
        string="Default Commission Rule",
        help="Default rule when no specific rule matches.",
    )

    def _get_default_commission_rule(self):
        self.ensure_one()

        if self.default_commission_rule_id:
            return self.default_commission_rule_id

        return self.env["pos.commission.rule"].search(
            [
                ("apply_on", "=", "global"),
                ("active", "=", True),
            ],
            limit=1,
            order="sequence",
        )

    @api.onchange("commission_enabled")
    def _onchange_commission_enabled(self):
        if self.commission_enabled:
            if not self.commission_journal_id:
                self.commission_journal_id = self.env["account.journal"].search(
                    [
                        ("type", "=", "general"),
                        ("company_id", "=", self.company_id.id),
                    ],
                    limit=1,
                )

    @api.model
    def _load_pos_data_fields(self, config):
        fields = super()._load_pos_data_fields(config)
        fields.append("commission_enabled")
        return fields
