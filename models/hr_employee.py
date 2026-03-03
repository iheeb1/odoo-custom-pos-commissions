# -*- coding: utf-8 -*-

from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    commission_enabled = fields.Boolean(
        string="Eligible for Commission",
        default=True,
        help="Check if this employee should receive sales commissions.",
    )

    commission_account_id = fields.Many2one(
        "account.account",
        string="Commission Account",
        domain=[("account_type", "=", "liability_current")],
        help="Account to credit for this employee's commissions.",
    )

    commission_line_ids = fields.One2many(
        "pos.commission.line", "employee_id", string="Commission Lines", readonly=True
    )

    commission_total = fields.Monetary(
        string="Total Commissions", compute="_compute_commission_totals", store=False
    )

    commission_paid = fields.Monetary(
        string="Paid Commissions", compute="_compute_commission_totals", store=False
    )

    commission_due = fields.Monetary(
        string="Due Commissions", compute="_compute_commission_totals", store=False
    )

    def _compute_commission_totals(self):
        for employee in self:
            lines = self.env["pos.commission.line"].search(
                [
                    ("employee_id", "=", employee.id),
                ]
            )
            employee.commission_total = sum(lines.mapped("commission_amount"))
            employee.commission_paid = sum(
                lines.filtered(lambda l: l.state == "paid").mapped("commission_amount")
            )
            employee.commission_due = sum(
                lines.filtered(lambda l: l.state == "posted").mapped(
                    "commission_amount"
                )
            )

    def _load_pos_data_fields(self, config):
        return ["id", "name", "work_email", "commission_enabled"]

    def _load_pos_data_domain(self, data, config):
        return [("company_id", "=", config.company_id.id)]
