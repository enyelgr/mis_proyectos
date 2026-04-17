from odoo import models, fields, api
from odoo.exceptions import UserError

class GymHorarioChangeWizard(models.TransientModel):
    _name = 'gym.horario.change.wizard'
    _description = 'Validación de Cambio de Horario'

    horario_id = fields.Many2one('gym.horario', required=True)
    fecha = fields.Date(string='Nueva Fecha', required=True)
    hora_inicio = fields.Float(string='Nueva Hora Inicio (0-24)', required=True)
    hora_fin = fields.Float(string='Nueva Hora Fin (0-24)', required=True)
    area = fields.Selection([
        ('1', 'Área 1'),
        ('2', 'Área 2'),
        ('3', 'Área 3'),
        ('4', 'Área 4'),
    ], string='Nueva Área', required=True)
    
    status_message = fields.Text(string='Estado', readonly=True)
    is_valid = fields.Boolean(default=False)

    @api.onchange('fecha', 'hora_inicio', 'hora_fin', 'area')
    def _check_disponibilidad(self):
        for rec in self:
            if not rec.fecha or rec.hora_inicio is None or rec.hora_fin is None or not rec.area:
                rec.status_message = "Por favor ingresa todos los datos para validar."
                rec.is_valid = False
                continue

            domain = [
                ('id', '!=', rec.horario_id.id),
                ('area', '=', rec.area),
                ('fecha', '=', rec.fecha),
                ('state', '!=', 'cancelado'),
                ('hora_inicio', '<', rec.hora_fin),
                ('hora_fin', '>', rec.hora_inicio),
            ]
            conflict = self.env['gym.horario'].search(domain, limit=1)
            if conflict:
                area_name = dict(self.env['gym.horario']._fields['area'].selection).get(rec.area)
                rec.status_message = f"❌ ALERTA DE CRUCE: Ya existe una clase ({conflict.name}) en {area_name} el {rec.fecha} a esa hora."
                rec.is_valid = False
            else:
                rec.status_message = "✅ HORARIO DISPONIBLE: Puedes aplicar el cambio de horario sin problemas."
                rec.is_valid = True

    def action_apply_change(self):
        if not self.is_valid:
            raise UserError("No se puede aplicar un horario que genera conflicto. Revisa los datos y vuelve a intentar.")
        self.horario_id.write({
            'fecha': self.fecha,
            'hora_inicio': self.hora_inicio,
            'hora_fin': self.hora_fin,
            'area': self.area
        })
        return {'type': 'ir.actions.act_window_close'}
