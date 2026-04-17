# business_hub_360/wizard/report_wizard.py
from odoo import models, fields, api


class ReportWizard(models.TransientModel):
    _name = 'bh360.report.wizard'
    _description = 'Asistente de Reportes'
    
    report_type = fields.Selection([
        ('financial', 'Financiero'),
        ('inventory', 'Inventario'),
        ('sales', 'Ventas'),
        ('hr', 'RRHH'),
    ], string='Tipo de Reporte', required=True)

    date_from = fields.Date(string='Fecha Desde', required=True)
    date_to = fields.Date(string='Fecha Hasta', required=True)
    
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    
    def action_generate_report(self):
        """Generar reporte"""
        self.ensure_one()
        # Aquí iría la lógica para generar el reporte
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Reporte Generado',
                'message': f'Reporte {self.report_type} generado exitosamente',
                'type': 'success',
                'sticky': False,
            }
        }
