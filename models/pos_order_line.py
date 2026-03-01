# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosOrderLine(models.Model):
    _name = "pos.order.line"
    _inherit = ["pos.order.line", "pos.load.mixin"]

    commission_employee_id = fields.Many2one(
        "hr.employee",
        string="Commission Employee",
        help="Employee who will receive commission for this line. Defaults to order cashier.",
    )

    commission_amount = fields.Monetary(
        string="Commission", compute="_compute_commission_amount", store=True
    )

    @api.depends(
        "product_id",
        "qty",
        "price_subtotal",
        "commission_employee_id",
        "order_id.employee_id",
    )
    def _compute_commission_amount(self):
        for line in self:
            commission = 0.0

            if not line.order_id.config_id.commission_enabled:
                line.commission_amount = commission
                continue

            employee = (
                line.commission_employee_id
                or line.order_id.employee_id
                or line.order_id.user_id.employee_id
            )

            if not employee or not employee.commission_enabled:
                line.commission_amount = commission
                continue

            rule = line.env["pos.commission.rule"].get_applicable_rule(
                product=line.product_id,
                employee=employee,
                pos_config=line.order_id.config_id,
                date=line.order_id.date_order.date()
                if line.order_id.date_order
                else None,
            )

            if not rule:
                rule = line.order_id.config_id._get_default_commission_rule()

            if rule:
                calc_base = rule.calc_base
                if line.order_id.config_id.commission_calc_base:
                    calc_base = line.order_id.config_id.commission_calc_base

                if calc_base == "after_discount":
                    base_amount = line.price_subtotal
                else:
                    base_amount = line.price_unit * line.qty

                commission = rule.calculate_commission(base_amount, line.qty)

            line.commission_amount = commission

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super(PosOrderLine, self)._load_pos_data_fields(config_id)
        return fields + ["commission_employee_id", "commission_amount"]
