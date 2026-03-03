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
            lineEmployees: initialAssignments
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
        const result = await super.askBeforeValidation(...arguments);
        
        if (result === false) {
            return false;
        }
        
        if (!this.pos.config.commission_enabled) {
            return true;
        }
        
        const order = this.order;
        
        if (!order || !order.lines || order.lines.length === 0) {
            return true;
        }
        
        const employees = this.pos.models["hr.employee"].getAll();
        
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
        
        for (const line of order.lines) {
            const employeeId = popupResult[line.uuid];
            if (employeeId) {
                const employee = this.pos.models["hr.employee"].get(employeeId);
                if (employee) {
                    line.commission_employee_id = employee;
                }
            }
        }
        
        return true;
    },
});
