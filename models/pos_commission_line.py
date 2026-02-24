# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from collections import defaultdict


class PosCommissionLine(models.Model):
    _name = "pos.commission.line"
    _description = "POS Commission Line"
    _order = "date desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code(
            "pos.commission.line"
        ),
    )

    employee_id = fields.Many2one(
        "hr.employee", string="Employee", required=True, index=True
    )

    order_id = fields.Many2one(
        "pos.order", string="POS Order", required=False, index=True, ondelete="cascade"
    )

    pos_config_id = fields.Many2one(
        "pos.config",
        string="POS Location",
        index=True,
    )

    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        readonly=True,
        help="Journal used for this commission entry",
    )

    order_line_id = fields.Many2one(
        "pos.order.line", string="POS Order Line", ondelete="cascade"
    )

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        related="order_line_id.product_id",
        store=True,
    )

    qty = fields.Float(string="Quantity", related="order_line_id.qty", store=True)

    base_amount = fields.Monetary(
        string="Base Amount",
        required=True,
        help="Amount used as base for commission calculation",
    )

    commission_type = fields.Selection(
        [
            ("percentage", "Percent"),
            ("fixed_per_piece", "Per Item"),
            ("fixed_per_order", "Per Order"),
            ("fixed_after_threshold", "Tiered"),
        ],
        string="Commission Type",
        required=True,
    )

    rate = fields.Float(string="Amount", required=True)

    cumulative_qty = fields.Float(
        string="Cumulative Quantity",
        help="Total quantity sold by employee before this order (for threshold calculation)",
    )

    commission_amount = fields.Monetary(
        string="Commission Amount", required=True, help="Final commission amount"
    )

    rule_id = fields.Many2one("pos.commission.rule", string="Rule Applied")

    state = fields.Selection(
        [
            ("posted", "Posted"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="posted",
        required=True,
        index=True,
    )

    payment_move_id = fields.Many2one(
        "account.move", string="Payment Entry", readonly=True
    )

    journal_entry_id = fields.Many2one(
        "account.move.line", string="Journal Entry Line", readonly=True
    )

    move_id = fields.Many2one("account.move", string="Journal Entry", readonly=True)

    cancel_move_id = fields.Many2one(
        "account.move", string="Cancellation Entry", readonly=True
    )

    date = fields.Date(string="Date", required=True, default=fields.Date.context_today)

    company_id = fields.Many2one(
        "res.company", string="Company", related="order_id.company_id", store=True
    )

    currency_id = fields.Many2one(
        "res.currency", string="Currency", related="company_id.currency_id"
    )

    note = fields.Text(string="Notes")

    def action_cancel(self):
        for line in self:
            if line.state != "posted":
                continue
            if line.cancel_move_id:
                continue

            if not line.move_id:
                line.write({"state": "cancelled"})
                continue

            cancel_move = self.env["account.move"].create(
                {
                    "journal_id": line.journal_id.id,
                    "date": fields.Date.today(),
                    "ref": _("Commission Cancellation: %s") % line.name,
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": _("Cancellation: %s")
                                % line.move_id.line_ids[0].name,
                                "account_id": line.move_id.line_ids[0].account_id.id,
                                "debit": line.move_id.line_ids[0].credit,
                                "credit": line.move_id.line_ids[0].debit,
                                "partner_id": line.move_id.line_ids[0].partner_id.id,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": _("Cancellation: %s")
                                % line.move_id.line_ids[1].name
                                if len(line.move_id.line_ids) > 1
                                else _("Cancellation"),
                                "account_id": line.move_id.line_ids[1].account_id.id
                                if len(line.move_id.line_ids) > 1
                                else line.journal_id.default_account_id.id,
                                "debit": line.move_id.line_ids[1].credit
                                if len(line.move_id.line_ids) > 1
                                else line.commission_amount,
                                "credit": line.move_id.line_ids[1].debit
                                if len(line.move_id.line_ids) > 1
                                else 0.0,
                                "partner_id": line.move_id.line_ids[1].partner_id.id
                                if len(line.move_id.line_ids) > 1
                                else False,
                            },
                        ),
                    ],
                }
            )
            cancel_move.action_post()

            line.write(
                {
                    "state": "cancelled",
                    "cancel_move_id": cancel_move.id,
                }
            )

        return True

    def action_mark_paid(self, payment_move_id):
        self.write(
            {
                "state": "paid",
                "payment_move_id": payment_move_id,
            }
        )
        return True

    @api.model
    def create_commission_lines(self, order):
        if not order.config_id.commission_enabled:
            return self.env["pos.commission.line"]

        commission_lines = self.env["pos.commission.line"]
        employees_commissions = defaultdict(
            lambda: {
                "lines": self.env["pos.commission.line"],
                "total": 0.0,
                "cumulative_qty": {},
            }
        )

        for order_line in order.lines:
            employee = (
                order_line.commission_employee_id
                or order.employee_id
                or order.user_id.employee_id
            )
            if not employee:
                continue

            if not employee.commission_enabled:
                continue

            rule = self.env["pos.commission.rule"].get_applicable_rule(
                product=order_line.product_id,
                employee=employee,
                pos_config=order.config_id,
                date=order.date_order.date(),
            )

            if not rule:
                rule = order.config_id._get_default_commission_rule()

            if not rule:
                continue

            calc_base = rule.calc_base
            if order.config_id.commission_calc_base:
                calc_base = order.config_id.commission_calc_base

            if calc_base == "after_discount":
                base_amount = order_line.price_subtotal
            else:
                base_amount = order_line.price_unit * order_line.qty

            cumulative_qty = employees_commissions[employee]["cumulative_qty"].get(
                rule.id, 0.0
            )
            previous_commissions = self.search(
                [
                    ("employee_id", "=", employee.id),
                    ("rule_id", "=", rule.id),
                    ("state", "=", "posted"),
                ]
            )
            if previous_commissions:
                cumulative_qty = sum(previous_commissions.mapped("qty"))

            cumulative_qty_before = cumulative_qty
            cumulative_qty += order_line.qty

            commission_amount = rule.calculate_commission(
                base_amount, order_line.qty, cumulative_qty_before
            )

            if commission_amount <= 0:
                continue

            commission_line = self.create(
                {
                    "employee_id": employee.id,
                    "order_id": order.id,
                    "order_line_id": order_line.id,
                    "pos_config_id": order.config_id.id,
                    "base_amount": base_amount,
                    "commission_type": rule.commission_type,
                    "rate": rule.rate,
                    "commission_amount": commission_amount,
                    "rule_id": rule.id,
                    "date": order.date_order.date(),
                    "qty": order_line.qty,
                    "cumulative_qty": cumulative_qty_before,
                    "state": "posted",
                }
            )

            commission_lines |= commission_line
            employees_commissions[employee]["lines"] |= commission_line
            employees_commissions[employee]["total"] += commission_amount
            employees_commissions[employee]["cumulative_qty"][rule.id] = cumulative_qty

        return commission_lines, employees_commissions

    @api.model
    def create_journal_entry(self, order, commission_lines, employees_commissions):
        if not commission_lines:
            return self.env["account.move"]

        if not order.config_id.commission_journal_id:
            return self.env["account.move"]

        journal = order.config_id.commission_journal_id
        expense_account = order.config_id.commission_expense_account_id

        if not expense_account:
            expense_account = journal.default_account_id

        if not expense_account:
            return self.env["account.move"]

        move_lines = []
        total_commission = 0.0

        for employee, data in employees_commissions.items():
            if data["total"] <= 0:
                continue

            liability_account = employee.commission_account_id
            if not liability_account:
                liability_account = order.config_id.commission_liability_account_id

            if not liability_account:
                continue

            total_commission += data["total"]

            move_lines.append(
                (
                    0,
                    0,
                    {
                        "name": _("Commission: %s - Order %s")
                        % (employee.name, order.name),
                        "account_id": liability_account.id,
                        "credit": data["total"],
                        "debit": 0.0,
                        "partner_id": employee.user_id.partner_id.id
                        if employee.user_id
                        else False,
                    },
                )
            )

        if total_commission <= 0 or not move_lines:
            return self.env["account.move"]

        move_lines.insert(
            0,
            (
                0,
                0,
                {
                    "name": _("Commissions: %s") % order.name,
                    "account_id": expense_account.id,
                    "debit": total_commission,
                    "credit": 0.0,
                },
            ),
        )

        move = self.env["account.move"].create(
            {
                "journal_id": journal.id,
                "date": order.date_order.date(),
                "ref": _("POS Commissions: %s") % order.name,
                "line_ids": move_lines,
            }
        )

        move.action_post()

        commission_lines.write(
            {
                "journal_entry_id": move.line_ids[0].id,
                "move_id": move.id,
                "journal_id": journal.id,
            }
        )

        return move
