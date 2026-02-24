# -*- coding: utf-8 -*-
{
    "name": "POS Sales Commission",
    "version": "1.0.0",
    "category": "Sales/Point of Sale",
    "summary": "Manage sales commissions for POS workers",
    "description": """
        POS Sales Commission Module
        ===========================
        
        Features:
        - Assign workers to POS order lines (defaults to session cashier)
        - Multiple commission types: percentage, fixed per piece, fixed per order
        - Flexible rule hierarchy: Product → Category → Employee → Global
        - Choose commission base: before or after discount
        - Automatic journal entry creation on order payment
        - Multi-employee order support with split commissions
        - Comprehensive reporting per employee and period
    """,
    "author": "Custom Development",
    "website": "",
    "license": "LGPL-3",
    "depends": [
        "web",
        "point_of_sale",
        "hr",
        "account",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "data/assets.xml",
        "views/pos_commission_rule_views.xml",
        "wizards/pos_commission_pay_wizard_views.xml",
        "views/pos_commission_line_views.xml",
        "views/pos_config_views.xml",
        "views/pos_order_views.xml",
        "views/hr_employee_views.xml",
        "views/product_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_sales_commission/static/src/js/pos_commission.js",
            "pos_sales_commission/static/src/xml/pos_commission.xml",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
