/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
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
            initialAssignments[line.uuid] = line.commission_employee_id || null;
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

patch(PosOrderline.prototype, {
    setup(vals) {
        super.setup(...arguments);
        this.commission_employee_id = vals?.commission_employee_id || null;
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.commission_employee_id = this.commission_employee_id || false;
        return json;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.commission_employee_id = json.commission_employee_id || null;
    },
});

patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(...arguments);
        this.employee_id = vals?.employee_id || null;
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.employee_id = this.employee_id || false;
        return json;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.employee_id = json.employee_id || null;
    },
});

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
            if (employeeId !== undefined) {
                line.commission_employee_id = employeeId;
            }
        }
        
        return true;
    },
});
