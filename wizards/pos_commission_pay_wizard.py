# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from collections import defaultdict


class PosCommissionPayWizard(models.TransientModel):
    _name = "pos.commission.pay.wizard"
    _description = "Pay Commissions Wizard"

    commission_line_ids = fields.Many2many(
        "pos.commission.line", string="Commission Lines", required=True
    )

    journal_id = fields.Many2one(
        "account.journal",
        string="Payment Journal",
        domain=[("type", "in", ("bank", "cash"))],
        required=True,
    )

    payment_date = fields.Date(
        string="Payment Date", required=True, default=fields.Date.context_today
    )

    total_amount = fields.Monetary(
        string="Total Amount", compute="_compute_total_amount"
    )

    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    currency_id = fields.Many2one(
        "res.currency", string="Currency", related="company_id.currency_id"
    )

    @api.depends("commission_line_ids.commission_amount")
    def _compute_total_amount(self):
        for wizard in self:
            wizard.total_amount = sum(
                wizard.commission_line_ids.mapped("commission_amount")
            )

    @api.model
    def default_get(self, fields_list):
        res = super(PosCommissionPayWizard, self).default_get(fields_list)

        active_ids = self.env.context.get("active_ids", [])
        if active_ids:
            lines = self.env["pos.commission.line"].browse(active_ids)
            posted_lines = lines.filtered(lambda l: l.state == "posted")
            if posted_lines:
                res["commission_line_ids"] = [(6, 0, posted_lines.ids)]

        journal = self.env["account.journal"].search(
            [
                ("type", "=", "bank"),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        if journal:
            res["journal_id"] = journal.id

        return res

    def action_pay(self):
        self.ensure_one()

        lines_to_pay = self.commission_line_ids.filtered(lambda l: l.state == "posted")
        if not lines_to_pay:
            raise UserError(_("No posted commission lines to pay."))

        employees_totals = defaultdict(float)
        for line in lines_to_pay:
            employees_totals[line.employee_id] += line.commission_amount

        move_lines = []
        for employee, total in employees_totals.items():
            if total <= 0:
                continue

            liability_account = employee.commission_account_id
            if not liability_account:
                liability_account = (
                    self.env["pos.config"]
                    .search([], limit=1)
                    .commission_liability_account_id
                )

            if not liability_account:
                raise UserError(
                    _("No liability account configured for employee %s") % employee.name
                )

            move_lines.append(
                (
                    0,
                    0,
                    {
                        "name": _("Commission Payment: %s") % employee.name,
                        "account_id": liability_account.id,
                        "debit": 0.0,
                        "credit": total,
                        "partner_id": employee.user_id.partner_id.id
                        if employee.user_id
                        else False,
                    },
                )
            )

        if not move_lines:
            raise UserError(_("No valid commission lines to pay."))

        payment_account = (
            self.journal_id.payment_credit_account_id
            or self.journal_id.default_account_id
        )
        if not payment_account:
            raise UserError(
                _("No payment account configured for the selected journal.")
            )

        move_lines.insert(
            0,
            (
                0,
                0,
                {
                    "name": _("Commission Payments"),
                    "account_id": payment_account.id,
                    "debit": self.total_amount,
                    "credit": 0.0,
                },
            ),
        )

        move = self.env["account.move"].create(
            {
                "journal_id": self.journal_id.id,
                "date": self.payment_date,
                "ref": _("Commission Payments"),
                "line_ids": move_lines,
            }
        )

        move.action_post()

        lines_to_pay.action_mark_paid(move.id)

        return {
            "type": "ir.actions.act_window_close",
        }
