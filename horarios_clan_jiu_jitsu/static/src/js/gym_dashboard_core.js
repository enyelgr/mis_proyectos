/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

export class GymDashboard extends Component {
    static template = "horarios_clan_jiu_jitsu.Dashboard";
    
    setup() {
        this.action = useService("action");
    }

    openArea(areaId) {
        this.action.doAction(`horarios_clan_jiu_jitsu.action_horarios_area_${areaId}`, {
            clearBreadcrumbs: false,
            viewType: "kanban"
        });
    }

    openAISensei() {
        this.action.doAction("horarios_clan_jiu_jitsu.action_ai_sensei_hub");
    }
}

registry.category("actions").add("gym_dashboard_client_action", GymDashboard);
