/** @odoo-module **/

import { registry } from "@web/core/registry";
import { calendarView } from "@web/views/calendar/calendar_view";
import { CalendarRenderer } from "@web/views/calendar/calendar_renderer";

import { patch } from "@web/core/utils/patch";
import { renderToElement } from "@web/core/utils/render";
import { CalendarCommonRenderer } from "@web/views/calendar/calendar_common/calendar_common_renderer";
import { CalendarCommonPopover } from "@web/views/calendar/calendar_common/calendar_common_popover";

/**
 * GYM CALENDAR RENDERER (Premium)
 * Implementamos el renderizado de la tarjeta "Dojo Badge"
 */
export class GymCalendarRenderer extends CalendarRenderer {
    /**
     * Sobrescribimos las opciones de FullCalendar para inyectar nuestro diseño
     */
    get fcOptions() {
        const options = super.fcOptions;
        if (this.props.model.resModel === "gym.horario") {
            const originalEventContent = options.eventContent;
            options.eventContent = (arg) => {
                // Si el bloque es muy pequeño (menos de 30 min), usamos el renderizado estándar
                // para evitar desbordamientos, de lo contrario usamos nuestro Badge Premium.
                const duration = arg.event.end - arg.event.start;
                if (duration < 1800000) { // Menos de 30 minutos
                    return originalEventContent ? originalEventContent(arg) : {};
                }

                try {
                    const element = renderToElement("horarios_clan_jiu_jitsu.CalendarEvent", {
                        record: arg.event.extendedProps.record,
                        rawRecord: arg.event.extendedProps.record,
                    });
                    return { domNodes: [element] };
                } catch (e) {
                    console.error("Error rendering Gym Calendar Event:", e);
                    return originalEventContent ? originalEventContent(arg) : {};
                }
            };
        }
        return options;
    }
}

// Parcheamos las opciones globales del calendario (horarios, lectura única)
patch(CalendarCommonRenderer.prototype, {
    get options() {
        const _super = super.options;
        if (this.props.model.resModel === "gym.horario") {
            return {
                ..._super,
                slotMinTime: "06:00:00",
                slotMaxTime: "21:30:00",
                slotDuration: "00:30:00",
                slotLabelInterval: "00:30:00",
                nowIndicator: false,
                editable: false,
                selectable: false,
                slotLabelFormat: [
                    {
                        hour: "numeric",
                        minute: "2-digit",
                        omitZeroMinute: true,
                        meridiem: "short",
                        hour12: true,
                    }
                ],
                eventTimeFormat: {
                    hour: "numeric",
                    minute: "2-digit",
                    meridiem: "short",
                    hour12: true,
                }
            };
        }
        return _super;
    }
});

// Parcheamos el Popover para mantener la seguridad y el perfil premium al hacer clic
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
    Renderer: GymCalendarRenderer,
};

registry.category("views").add("gym_calendar", gymCalendarView);
