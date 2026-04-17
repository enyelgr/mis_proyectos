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
        
        return {
            'doc_ids': docids,
            'doc_model': 'gym.horario.report.wizard',
            'data': data,
            'area_name': area_name,
            'hours_range': range(6, 22), # 6 AM to 9 PM (21:59)
            'horarios': horarios,
        }
