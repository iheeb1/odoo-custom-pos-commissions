# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PosCommissionRule(models.Model):
    _name = "pos.commission.rule"
    _description = "POS Commission Rule"
    _order = "sequence, id"

    name = fields.Char(string="Rule Name", required=True, translate=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10, help="Lower sequence = higher priority")

    commission_type = fields.Selection(
        [
            ("percentage", "Sales Percentage (نسبة من المبيعات)"),
            ("fixed_per_piece", "Per Unit (لكل وحدة)"),
            ("fixed_per_order", "Per Sale (لكل عملية بيع)"),
            ("fixed_after_threshold", "Tiered by Quantity (تصاعدي بالكميات)"),
        ],
        string="Commission Type",
        required=True,
        default="percentage",
    )

    rate = fields.Float(
        string="Amount",
        required=True,
        default=0.0,
        help="For Percent: 5.0 means 5%. For Per Item/Per Order: the fixed amount.",
    )

    threshold_qty = fields.Integer(
        string="Threshold Quantity",
        default=10,
        help="Cumulative quantity needed before commission applies (infinite if empty).",
    )

    threshold_rate = fields.Float(
        string="Commission Rate",
        default=2.0,
        help="Fixed amount per item AFTER threshold is reached.",
    )

    calc_base = fields.Selection(
        [
            ("after_discount", "After Discount"),
            ("before_discount", "Before Discount"),
        ],
        string="Calculation Base",
        default="after_discount",
        help="Calculate commission on price before or after discount is applied.",
    )

    apply_on = fields.Selection(
        [
            ("global", "Global (All Products)"),
            ("product_category", "Product Categories"),
            ("product", "Specific Products"),
        ],
        string="Apply On",
        required=True,
        default="global",
    )

    category_ids = fields.Many2many(
        "product.category",
        "pos_commission_rule_category_rel",
        "rule_id",
        "category_id",
        string="Product Categories",
    )

    product_ids = fields.Many2many(
        "product.product",
        "pos_commission_rule_product_rel",
        "rule_id",
        "product_id",
        string="Products",
    )

    employee_ids = fields.Many2many(
        "hr.employee",
        "pos_commission_rule_employee_rel",
        "rule_id",
        "employee_id",
        string="Employees",
        help="Leave empty to apply to all employees.",
    )

    pos_config_ids = fields.Many2many(
        "pos.config",
        "pos_commission_rule_config_rel",
        "rule_id",
        "config_id",
        string="Point of Sale",
        help="Leave empty to apply to all POS configurations.",
    )

    date_from = fields.Date(string="Valid From")
    date_to = fields.Date(string="Valid To")

    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rule in self:
            if rule.date_from and rule.date_to and rule.date_from > rule.date_to:
                raise ValidationError(
                    _("Valid From date must be before Valid To date.")
                )

    @api.constrains("rate")
    def _check_rate(self):
        for rule in self:
            if rule.rate < 0:
                raise ValidationError(_("Rate must be non-negative."))
            if rule.commission_type == "percentage" and rule.rate > 100:
                raise ValidationError(_("Percentage rate cannot exceed 100%."))

    def _is_valid_for(self, product, employee, pos_config, date=None):
        self.ensure_one()

        if not self.active:
            return False

        if self.date_from and date and date < self.date_from:
            return False
        if self.date_to and date and date > self.date_to:
            return False

        if self.employee_ids and employee.id not in self.employee_ids.ids:
            return False

        if self.pos_config_ids and pos_config.id not in self.pos_config_ids.ids:
            return False

        if self.apply_on == "global":
            return True
        elif self.apply_on == "product_category":
            if not self.category_ids:
                return True
            category = product.categ_id
            while category:
                if category.id in self.category_ids.ids:
                    return True
                category = category.parent_id
            return False
        elif self.apply_on == "product":
            if not self.product_ids:
                return True
            return product.id in self.product_ids.ids

        return True

    def get_applicable_rule(self, product, employee, pos_config, date=None):
        rules = self.search(
            [
                ("active", "=", True),
            ],
            order="sequence, id",
        )

        for rule in rules:
            if rule._is_valid_for(product, employee, pos_config, date):
                return rule

        return None

    def calculate_commission(self, base_amount, qty=1, cumulative_qty=0):
        self.ensure_one()

        if self.commission_type == "percentage":
            return base_amount * (self.rate / 100.0)
        elif self.commission_type == "fixed_per_piece":
            return self.rate * qty
        elif self.commission_type == "fixed_per_order":
            return self.rate
        elif self.commission_type == "fixed_after_threshold":
            if not self.threshold_qty:
                return self.threshold_rate * qty
            if cumulative_qty >= self.threshold_qty:
                return self.threshold_rate * qty
            remaining_threshold = self.threshold_qty - cumulative_qty
            if qty > remaining_threshold:
                excess_qty = qty - remaining_threshold
                return self.threshold_rate * excess_qty
            return 0.0

        return 0.0
