/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";

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
        const initialAssignments = {};
        for (const line of this.props.order.lines) {
            initialAssignments[line.uuid] = line.commission_employee_id?.id || null;
        }
        this.state = useState({
            lineEmployees: initialAssignments,
        });
    }

    onSelectEmployee(ev) {
        const lineUuid = ev.target.dataset.lineUuid;
        const employeeId = ev.target.value ? parseInt(ev.target.value) : null;
        this.state.lineEmployees[lineUuid] = employeeId;
    }

    onConfirm() {
        this.props.getPayload(this.state.lineEmployees);
        this.props.close();
    }

    onCancel() {
        this.props.getPayload(null);
        this.props.close();
    }
}

patch(OrderPaymentValidation.prototype, {
    async askBeforeValidation() {
        console.log("[COMMISSION] askBeforeValidation START");
        const result = await super.askBeforeValidation(...arguments);

        if (result === false) {
            console.log("[COMMISSION] super returned false, aborting");
            return false;
        }

        const order = this.order;
        console.log("[COMMISSION] order:", order);
        if (!order || !order.lines || order.lines.length === 0) {
            console.log("[COMMISSION] no order or no lines, skipping");
            return true;
        }
        console.log("[COMMISSION] order lines count:", order.lines.length);

        const employeeModel = this.pos.models["hr.employee"];
        console.log("[COMMISSION] employeeModel:", employeeModel);
        if (!employeeModel) {
            console.log("[COMMISSION] no hr.employee model, skipping");
            return true;
        }

        const employees = employeeModel.getAll();
        console.log("[COMMISSION] employees:", employees, "count:", employees?.length);
        if (!employees || employees.length === 0) {
            console.log("[COMMISSION] no employees, skipping");
            return true;
        }

        console.log("[COMMISSION] about to show popup");
        const popupResult = await makeAwaitable(this.pos.dialog, CommissionWorkerPopup, {
            order: order,
            employees: employees,
        });

        if (popupResult === null || popupResult === undefined) {
            return false;
        }

        for (const line of order.lines) {
            const employeeId = popupResult[line.uuid];
            if (employeeId) {
                const employee = employeeModel.get(employeeId);
                if (employee) {
                    line.commission_employee_id = employee;
                }
            }
        }

        return true;
    },
});
