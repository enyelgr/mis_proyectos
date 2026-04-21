from odoo import models, api

class ReportHorarioArea(models.AbstractModel):
    _name = 'report.horarios_clan_jiu_jitsu.report_horario_semanal_template'
    _description = 'Prepara la data para la Cartelera PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        area_selected = data.get('area') if data else '1'
        
        # Get all scheduled classes for this area, ignoring 'cancelado'
        domain = [
            ('area', '=', area_selected),
            ('state', '!=', 'cancelado')
        ]
        horarios = self.env['gym.horario'].search(domain)
        area_name = dict(self.env['gym.horario']._fields['area'].selection).get(area_selected)
        days = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        matrix = []
        skip_cells = {day: 0 for day in days}

        def to_12h(h_float):
            hour_24 = int(h_float)
            minute = int((h_float % 1) * 60)
            period = 'AM' if hour_24 < 12 else 'PM'
            hour_12 = hour_24 % 12
            if hour_12 == 0:
                hour_12 = 12
            return '%d:%02d %s' % (hour_12, minute, period)

        # Build 30-min intervals from 6 AM to 9:00 PM
        intervals = [6.0 + (i * 0.5) for i in range(31)]
        
        for h_val in intervals:
            time_label = '%s - %s' % (to_12h(h_val), to_12h(h_val + 0.5))
            
            row_cells = []
            for day in days:
                if skip_cells[day] > 0:
                    skip_cells[day] -= 1
                    continue
                
                active_class = next((h for h in horarios if h.dia_semana == day and h.hora_inicio <= h_val and h.hora_fin > h_val), None)
                
                if active_class:
                    remaining_slots = int(round((active_class.hora_fin - h_val) / 0.5))
                    row_cells.append({
                        'type': 'class',
                        'rowspan': remaining_slots,
                        'instructor': active_class.instructor_id.name.upper(),
                        'discipline': active_class.instructor_especialidad.upper() if active_class.instructor_especialidad else 'JIU JITSU',
                        'time_range_str': '%s - %s' % (
                            to_12h(active_class.hora_inicio), 
                            to_12h(active_class.hora_fin)
                        ),
                    })
                    skip_cells[day] = remaining_slots - 1
                else:
                    row_cells.append({
                        'type': 'empty',
                        'rowspan': 1
                    })
            matrix.append({
                'time_label': time_label,
                'cells': row_cells
            })

        return {
            'doc_ids': docids,
            'doc_model': 'gym.horario.report.wizard',
            'data': data,
            'area_name': area_name,
            'matrix': matrix,
            'days': [day.capitalize() for day in days],
        }
