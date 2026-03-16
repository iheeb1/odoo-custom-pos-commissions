# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _load_pos_data_fields(self, config):
        fields = super()._load_pos_data_fields(config)
        fields_to_exclude = {'commission_line_ids', 'commission_total', 'commission_move_id'}
        return [f for f in fields if f not in fields_to_exclude]

    employee_id = fields.Many2one(
        "hr.employee",
        string="Worker/Employee",
        help="Employee/Worker assigned to this order for commission",
    )

    commission_line_ids = fields.One2many(
        "pos.commission.line", "order_id", string="Commission Lines", readonly=True
    )

    commission_total = fields.Monetary(
        string="Total Commission", compute="_compute_commission_total", store=True
    )

    commission_move_id = fields.Many2one(
        "account.move", string="Commission Journal Entry", readonly=True
    )

    @api.depends("commission_line_ids.commission_amount", "commission_line_ids.state")
    def _compute_commission_total(self):
        for order in self:
            order.commission_total = sum(
                order.commission_line_ids.filtered(
                    lambda l: l.state != "cancel"
                ).mapped("commission_amount")
            )

    def _process_saved_order(self, draft):
        res = super(PosOrder, self)._process_saved_order(draft)

        if not draft and self.config_id.commission_enabled:
            self._create_commissions()

        return res

    def _create_commissions(self):
        self.ensure_one()

        if self.commission_line_ids:
            return

        CommissionLine = self.env["pos.commission.line"]
        commission_lines, employees_commissions = (
            CommissionLine.create_commission_lines(self)
        )

        if commission_lines:
            move = CommissionLine.create_journal_entry(
                self, commission_lines, employees_commissions
            )
            if move:
                self.commission_move_id = move.id

    def action_pos_order_paid(self):
        res = super(PosOrder, self).action_pos_order_paid()
        return res

    def refund(self):
        res = super(PosOrder, self).refund()

        if isinstance(res, dict) and res.get("res_id"):
            refund_order = self.browse(res["res_id"])
            if self.commission_line_ids:
                for commission_line in self.commission_line_ids:
                    if commission_line.state == "posted":
                        self.env["pos.commission.line"].create(
                            {
                                "employee_id": commission_line.employee_id.id,
                                "order_id": refund_order.id,
                                "order_line_id": False,
                                "base_amount": -commission_line.base_amount,
                                "commission_type": commission_line.commission_type,
                                "rate": commission_line.rate,
                                "commission_amount": -commission_line.commission_amount,
                                "rule_id": commission_line.rule_id.id,
                                "date": refund_order.date_order.date(),
                                "note": f"Refund adjustment for commission {commission_line.name}",
                            }
                        )

        return res
