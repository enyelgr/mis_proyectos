from odoo import models, fields, api


class GymInstructor(models.Model):
    _name = 'gym.instructor'
    _description = 'Instructor de Disciplina'
    _order = 'name asc'

    name = fields.Char(string='Nombre Completo', required=True)
    especialidad = fields.Char(string='Disciplina / Especialidad', help='Ej: Jiu Jitsu, Yoga, Crossfit')
    email = fields.Char(string='Correo Electrónico')
    telefono = fields.Char(string='Teléfono')
    image = fields.Image(string='Foto')
    active = fields.Boolean(string='Activo', default=True)

    horario_ids = fields.One2many('gym.horario', 'instructor_id', string='Horarios Asignados')
    horas_actual_mes = fields.Float(string='Horas este mes', compute='_compute_reportes', store=True)
    faltas_actual_mes = fields.Integer(string='Faltas este mes', compute='_compute_reportes', store=True)
    horas_hoy = fields.Float(string='Horas hoy', compute='_compute_reportes', store=True)

    @api.depends('horario_ids.duration', 'horario_ids.state', 'horario_ids.fecha')
    def _compute_reportes(self):
        from datetime import datetime

        today = fields.Date.today()
        for rec in self:
            horas_mes = 0.0
            faltas = 0
            horas_hoy = 0.0
            for horario in rec.horario_ids:
                if not horario.fecha:
                    continue
                try:
                    # horario.fecha ya es un objeto date, no necesitamos strptime
                    fecha = horario.fecha
                except Exception:
                    continue
                if fecha.year == today.year and fecha.month == today.month:
                    if horario.state == 'cancelado':
                        faltas += 1
                    else:
                        horas_mes += horario.duration
                if fecha == today and horario.state != 'cancelado':
                    horas_hoy += horario.duration
            rec.horas_actual_mes = horas_mes
            rec.faltas_actual_mes = faltas
            rec.horas_hoy = horas_hoy

    def action_dummy(self):
        return True
