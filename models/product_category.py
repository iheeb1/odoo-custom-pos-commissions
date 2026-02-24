# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = "product.category"

    commission_rule_id = fields.Many2one(
        "pos.commission.rule",
        string="Commission Rule",
        domain=[("apply_on", "=", "product_category")],
        help="Commission rule for products in this category. Products can override this.",
    )

    commission_override_rate = fields.Float(
        string="Commission Override Rate",
        help="Override rate for products in this category.",
    )

    commission_override_type = fields.Selection(
        [
            ("none", "No Override"),
            ("percentage", "Percentage"),
            ("fixed", "Fixed Amount"),
        ],
        string="Override Type",
        default="none",
    )
