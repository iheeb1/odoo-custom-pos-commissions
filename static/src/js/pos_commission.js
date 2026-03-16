/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";

let _lastCommissionEmployee = "";

export class CommissionWorkerPopup extends Component {
    static template = "pos_sales_commission.CommissionWorkerPopup";
    static components = { Dialog };
    static props = {
        order: Object,
        employees: Array,
        getPayload: Function,
        close: Function,
    };

    setup() {
        this.state = useState({
            selectedEmployee: null,
        });
    }

    onSelectEmployee(ev) {
        this.state.selectedEmployee = ev.target.value ? parseInt(ev.target.value) : null;
    }

    onConfirm() {
        this.props.getPayload(this.state.selectedEmployee);
        this.props.close();
    }

    onCancel() {
        this.props.getPayload(null);
        this.props.close();
    }
}

patch(OrderPaymentValidation.prototype, {
    async askBeforeValidation() {
        const result = await super.askBeforeValidation(...arguments);

        if (result === false) {
            return false;
        }

        const order = this.order;
        if (!order || !order.lines || order.lines.length === 0) {
            return true;
        }

        const employeeModel = this.pos.models["hr.employee"];
        if (!employeeModel) {
            return true;
        }

        const employees = employeeModel.getAll();
        if (!employees || employees.length === 0) {
            return true;
        }

        const popupResult = await makeAwaitable(this.pos.dialog, CommissionWorkerPopup, {
            order: order,
            employees: employees,
        });

        if (popupResult === null || popupResult === undefined) {
            return false;
        }

        if (popupResult) {
            const employee = employeeModel.get(popupResult);
            if (employee) {
                _lastCommissionEmployee = employee.name;
                for (const line of order.lines) {
                    line.commission_employee_id = employee;
                }
            }
        } else {
            _lastCommissionEmployee = "";
        }

        return true;
    },
});

patch(OrderReceipt.prototype, {
    get commissionWorkerName() {
        return _lastCommissionEmployee;
    },
});
