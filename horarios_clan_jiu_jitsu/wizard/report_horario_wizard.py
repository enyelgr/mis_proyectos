from odoo import models, fields

class GymHorarioReportWizard(models.TransientModel):
    _name = 'gym.horario.report.wizard'
    _description = 'Wizard para Descargar PDF del Horario por Área'

    area = fields.Selection([
        ('1', 'Área 1'),
        ('2', 'Área 2'),
        ('3', 'Área 3'),
        ('4', 'Área 4'),
    ], string='Generar Cartelera Para:', required=True, default='1')

    def action_print_report(self):
        # We pass the selected area in the context or domain when generating the report
        data = {
            'area': self.area,
        }
        return self.env.ref('horarios_clan_jiu_jitsu.action_report_horario_semanal').report_action(self, data=data)
