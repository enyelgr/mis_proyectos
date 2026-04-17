/** @odoo-module **/

import { registry } from "@web/core/registry";
import { calendarView } from "@web/views/calendar/calendar_view";
import { CalendarRenderer } from "@web/views/calendar/calendar_renderer";
import { onMounted, onWillUnmount } from "@odoo/owl";

export class GymCalendarRenderer extends CalendarRenderer {
    setup() {
        super.setup();
        onMounted(() => {
            const contentNode = document.querySelector('.o_content');
            if (contentNode) contentNode.classList.add('clan_jiujitsu_watermark_container');
        });
        onWillUnmount(() => {
            const contentNode = document.querySelector('.o_content');
            if (contentNode) contentNode.classList.remove('clan_jiujitsu_watermark_container');
        });
    }

    get options() {
        const res = super.options;
        res.slotMinTime = "06:00:00";
        res.slotMaxTime = "22:00:00";
        return res;
    }
}

export const gymCalendarView = {
    ...calendarView,
    Renderer: GymCalendarRenderer,
};

registry.category("views").add("gym_calendar", gymCalendarView);
