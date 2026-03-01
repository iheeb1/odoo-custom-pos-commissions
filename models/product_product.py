# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "pos.load.mixin"]

    commission_rule_id = fields.Many2one(
        "pos.commission.rule",
        string="Commission Rule",
        domain=[("apply_on", "=", "product")],
        help="Specific commission rule for this product. Leave empty to use category or global rules.",
    )

    commission_override_rate = fields.Float(
        string="Commission Override Rate",
        help="Override the commission rate for this product. Set to 0 to disable commission.",
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

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super(ProductProduct, self)._load_pos_data_fields(config_id)
        if config_id:
            config = self.env["pos.config"].browse(config_id)
            if config.commission_enabled:
                fields = fields + [
                    "commission_rule_id",
                    "commission_override_rate",
                    "commission_override_type",
                ]
        return fields
