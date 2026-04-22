/** @odoo-module **/

import { registry } from "@web/core/registry";
import { calendarView } from "@web/views/calendar/calendar_view";
import { patch } from "@web/core/utils/patch";
import { CalendarCommonRenderer } from "@web/views/calendar/calendar_common/calendar_common_renderer";
import { CalendarCommonPopover } from "@web/views/calendar/calendar_common/calendar_common_popover";

// Parcheamos el Renderizador para inyectar HTML personalizado en los eventos
patch(CalendarCommonRenderer.prototype, {
    /**
     * @override
     */
    onEventContent(arg) {
        const { event } = arg;
        if (this.props.model.resModel === "gym.horario") {
            const name = event.title || "";
            const parts = name.split(" | ");
            
            const container = document.createElement("div");
            container.className = "dojo-event-tpl-container";

            if (parts.length > 1) {
                const discipline = parts[0];
                const instructor = parts[1];
                container.innerHTML = `
                    <div class="dojo-tpl-discipline">${discipline}</div>
                    <div class="dojo-tpl-instructor">${instructor}</div>
                `;
            } else {
                container.innerHTML = `<div class="dojo-tpl-full">${name}</div>`;
            }

            return { domNodes: [container] };
        }
        return super.onEventContent(arg);
    },

    get options() {
        const _super = super.options;
        if (this.props.model.resModel === "gym.horario") {
            return {
                ..._super,
                slotMinTime: "06:00:00",
                slotMaxTime: "22:00:00",
                slotDuration: "00:30:00",
                slotLabelInterval: "00:30:00",
                nowIndicator: false,
                editable: false,
                selectable: false,
                slotLabelContent: (arg) => {
                    const hours = arg.date.getHours();
                    const minutes = arg.date.getMinutes();
                    const ampm = hours >= 12 ? 'PM' : 'AM';
                    const h12 = hours % 12 || 12;
                    const hh = h12 < 10 ? '0' + h12 : h12;
                    const mm = minutes < 10 ? '0' + minutes : minutes;
                    return `${hh}:${mm} ${ampm}`;
                },
                slotLabelFormat: {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: true
                },
                eventTimeFormat: {
                    hour: 'numeric',
                    minute: '2-digit',
                    meridiem: 'short',
                    hour12: true,
                }
            };
        }
        return _super;
    }
});

// Parcheamos el Popover para mantener la seguridad
patch(CalendarCommonPopover.prototype, {
    get isEventEditable() {
        if (this.props.model.resModel === "gym.horario") {
            return false;
        }
        return this.props.model.canEdit;
    }
});

export const gymCalendarView = {
    ...calendarView,
};

registry.category("views").add("gym_calendar", gymCalendarView);
