# POS Sales Commission

An Odoo 19 module that assigns sales commissions to POS workers per order line, with automatic journal entries and reporting.

## Features

- Popup at payment validation to assign a worker to each order line
- Commission types: percentage, fixed per piece, fixed per order
- Rule hierarchy: Product → Category → Employee → Global default
- Commission base: amount before or after discount
- Automatic accounting entries on order sync
- Pay commissions via wizard (creates journal entry)
- Reporting per employee and date range

## Requirements

- Odoo 19
- Modules: `point_of_sale`, `hr`, `account`
- `pos_hr` recommended (installed automatically or manually)

## Installation

1. Copy the `pos_sales_commission` folder into your Odoo addons path.
2. Restart Odoo.
3. Go to `Apps`, search for **POS Sales Commission**, and install.

## Configuration

**Enable commissions on your POS:**
`Point of Sale → Configuration → Settings` → enable **Commission** → Save

**Create commission rules:**
`Point of Sale → Configuration → Commission Rules` → New

**Per-employee account (optional):**
`Employees → [Employee] → Commission tab` → set Commission Account

## Usage

When validating a POS payment, a popup appears to assign a worker to each order line. Leave blank to default to the session cashier. Confirm to proceed.

**Reports & Payouts:**
- `Point of Sale → Reporting → Commission Lines`
- `Point of Sale → Reporting → Pay Commission`

## File Structure

```
pos_sales_commission/
├── models/
│   ├── hr_employee.py          # Commission fields on employee
│   ├── pos_commission_line.py  # Commission record per order line
│   ├── pos_commission_rule.py  # Rule definitions
│   ├── pos_config.py           # POS config settings
│   ├── pos_order.py            # Commission creation on order sync
│   ├── pos_order_line.py       # commission_employee_id field
│   ├── pos_session.py          # Loads hr.employee into POS frontend
│   ├── product_category.py     # Per-category commission rule
│   └── product_product.py      # Per-product commission rule
├── static/src/
│   ├── js/pos_commission.js    # Worker assignment popup + validation hook
│   └── xml/pos_commission.xml  # OWL template for the popup
├── wizards/
│   └── pos_commission_pay_wizard.py
├── DOCS_AR.md                  # Arabic user guide
└── __manifest__.py
```

## License

LGPL-3
