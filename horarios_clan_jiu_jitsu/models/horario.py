from datetime import datetime, timedelta, time
import pytz

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class GymHorario(models.Model):
    _name = 'gym.horario'
    _description = 'Bloque de Horario de Clase'
    _order = 'fecha asc, hora_inicio asc, area asc'

    name = fields.Char(string='Referencia', compute='_compute_name', store=True)
    fecha = fields.Date(string='Fecha', required=True, default=fields.Date.today)
    fecha_hora_inicio = fields.Datetime(string='Fecha/Hora Inicio', compute='_compute_datetime', inverse='_inverse_datetime', store=True)
    fecha_hora_fin = fields.Datetime(string='Fecha/Hora Fin', compute='_compute_datetime', inverse='_inverse_datetime', store=True)
    dia_semana = fields.Selection([
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
        ('domingo', 'Domingo'),
    ], string='Día de la Semana', compute='_compute_dia_semana', inverse='_inverse_dia_semana', store=True, group_expand='_read_group_dia_semana')
    hora_inicio = fields.Float(string='Hora Inicio', compute='_compute_hora_inicio', inverse='_inverse_hora_inicio', store=True)
    hora_inicio_hora = fields.Integer(string='Hora (1-12)', default=9)
    hora_inicio_ampm = fields.Selection([('AM', 'AM'), ('PM', 'PM')], string='AM/PM', default='AM')
    hora_fin = fields.Float(string='Hora Fin', compute='_compute_hora_fin', inverse='_inverse_hora_fin', store=True)
    hora_fin_hora = fields.Integer(string='Hora (1-12)', default=10)
    hora_fin_ampm = fields.Selection([('AM', 'AM'), ('PM', 'PM')], string='AM/PM', default='AM')
    top_position = fields.Float(string='Posición vertical', compute='_compute_schedule_layout', store=True)
    block_height = fields.Float(string='Altura del bloque', compute='_compute_schedule_layout', store=True)
    hora_inicio_12h = fields.Char(string='Hora Inicio (12h)', compute='_compute_horas_12h')
    hora_fin_12h = fields.Char(string='Hora Fin (12h)', compute='_compute_horas_12h')
    duration = fields.Float(string='Duración (hrs)', compute='_compute_duration', store=True)
    area = fields.Selection([
        ('1', 'Área 1'),
        ('2', 'Área 2'),
        ('3', 'Área 3'),
        ('4', 'Área 4'),
    ], string='Área', required=True, default='1')
    instructor_id = fields.Many2one('gym.instructor', string='Instructor', required=True)
    state = fields.Selection([
        ('programado', 'Programado'),
        ('cancelado', 'Cancelado / Ausencia'),
        ('completado', 'Completado'),
    ], string='Estado', default='programado', tracking=True)

    @api.depends('fecha', 'hora_inicio', 'hora_fin')
    def _compute_datetime(self):
        user_tz_name = self.env.user.tz or self._context.get('tz') or 'UTC'
        try:
            user_tz = pytz.timezone(user_tz_name)
        except pytz.UnknownTimeZoneError:
            user_tz = pytz.utc
            
        for rec in self:
            if rec.fecha and rec.hora_inicio is not None and rec.hora_fin is not None:
                h_start, m_start = int(rec.hora_inicio), int((rec.hora_inicio % 1) * 60)
                h_fin, m_fin = int(rec.hora_fin), int((rec.hora_fin % 1) * 60)
                
                dt_start = datetime.combine(rec.fecha, time(hour=h_start, minute=m_start))
                dt_fin = datetime.combine(rec.fecha, time(hour=h_fin, minute=m_fin))
                
                rec.fecha_hora_inicio = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)
                rec.fecha_hora_fin = user_tz.localize(dt_fin).astimezone(pytz.utc).replace(tzinfo=None)
            else:
                rec.fecha_hora_inicio = False
                rec.fecha_hora_fin = False

    def _inverse_datetime(self):
        user_tz_name = self.env.user.tz or self._context.get('tz') or 'UTC'
        try:
            user_tz = pytz.timezone(user_tz_name)
        except pytz.UnknownTimeZoneError:
            user_tz = pytz.utc
            
        for rec in self:
            if rec.fecha_hora_inicio and rec.fecha_hora_fin:
                dt_start_utc = pytz.utc.localize(rec.fecha_hora_inicio)
                dt_start_user = dt_start_utc.astimezone(user_tz)
                
                dt_fin_utc = pytz.utc.localize(rec.fecha_hora_fin)
                dt_fin_user = dt_fin_utc.astimezone(user_tz)
                
                rec.fecha = dt_start_user.date()
                rec.hora_inicio = dt_start_user.hour + dt_start_user.minute / 60.0
                rec.hora_fin = dt_fin_user.hour + dt_fin_user.minute / 60.0

    @api.constrains('hora_inicio', 'hora_fin')
    def _check_hours(self):
        for record in self:
            if record.hora_fin <= record.hora_inicio:
                raise ValidationError('La hora de fin debe ser mayor que la hora de inicio.')

    @api.constrains('hora_inicio_hora', 'hora_fin_hora')
    def _check_hora_range(self):
        for record in self:
            if record.hora_inicio_hora and (record.hora_inicio_hora < 1 or record.hora_inicio_hora > 12):
                raise ValidationError('La hora de inicio debe estar entre 1 y 12.')
            if record.hora_fin_hora and (record.hora_fin_hora < 1 or record.hora_fin_hora > 12):
                raise ValidationError('La hora de fin debe estar entre 1 y 12.')

    @api.constrains('area', 'fecha', 'hora_inicio', 'hora_fin', 'state')
    def _check_overlap(self):
        for record in self:
            if record.state == 'cancelado':
                continue
            domain = [
                ('id', '!=', record.id),
                ('area', '=', record.area),
                ('fecha', '=', record.fecha),
                ('state', '!=', 'cancelado'),
                ('hora_inicio', '<', record.hora_fin),
                ('hora_fin', '>', record.hora_inicio),
            ]
            if self.search(domain):
                area_name = dict(self._fields['area'].selection).get(record.area)
                raise ValidationError('¡Conflicto de Horario! Ya existe una clase en %s el %s a esa hora.' % (area_name, record.fecha))

    @api.depends('fecha')
    def _compute_dia_semana(self):
        mapping = {
            0: 'lunes',
            1: 'martes',
            2: 'miercoles',
            3: 'jueves',
            4: 'viernes',
            5: 'sabado',
            6: 'domingo',
        }
        for rec in self:
            if rec.fecha:
                rec.dia_semana = mapping[rec.fecha.weekday()]
            else:
                rec.dia_semana = False

    def _inverse_dia_semana(self):
        mapping = {
            'lunes': 0,
            'martes': 1,
            'miercoles': 2,
            'jueves': 3,
            'viernes': 4,
            'sabado': 5,
            'domingo': 6,
        }
        for rec in self:
            if rec.fecha and rec.dia_semana:
                current_weekday = rec.fecha.weekday()
                target_weekday = mapping.get(rec.dia_semana, current_weekday)
                if current_weekday != target_weekday:
                    diff = target_weekday - current_weekday
                    rec.fecha = rec.fecha + timedelta(days=diff)

    @api.model
    def _read_group_dia_semana(self, *args, **kwargs):
        return [
            'lunes', 'martes', 'miercoles', 'jueves',
            'viernes', 'sabado', 'domingo'
        ]

    @api.depends('fecha', 'hora_inicio', 'area', 'instructor_id')
    def _compute_name(self):
        for rec in self:
            if rec.fecha and rec.area and rec.hora_inicio is not None:
                h_start = int(rec.hora_inicio)
                m_start = int((rec.hora_inicio - h_start) * 60)
                area_name = dict(self._fields['area'].selection).get(rec.area)
                rec.name = '%s %02d:%02d - %s (%s)' % (
                    rec.fecha,
                    h_start,
                    m_start,
                    area_name,
                    rec.instructor_id.name if rec.instructor_id else 'Sin instructor',
                )
            else:
                rec.name = 'Nuevo Bloque'

    @api.depends('hora_inicio', 'hora_fin')
    def _compute_duration(self):
        for rec in self:
            if rec.hora_inicio is not None and rec.hora_fin is not None:
                rec.duration = rec.hora_fin - rec.hora_inicio
            else:
                rec.duration = 0.0

    @api.depends('hora_inicio', 'hora_fin')
    def _compute_schedule_layout(self):
        start_hour = 6.0
        hour_height = 40.0
        max_height = (21.0 - start_hour) * hour_height
        for rec in self:
            if rec.hora_inicio is not None and rec.hora_fin is not None:
                start = min(max(rec.hora_inicio, start_hour), 21.0)
                duration = max(rec.hora_fin - rec.hora_inicio, 0.25)
                rec.top_position = (start - start_hour) * hour_height
                rec.block_height = min(duration * hour_height, max_height - rec.top_position)
            else:
                rec.top_position = 0.0
                rec.block_height = 0.0

    @api.depends('hora_inicio_hora', 'hora_inicio_ampm')
    def _compute_hora_inicio(self):
        for rec in self:
            if rec.hora_inicio_hora and rec.hora_inicio_ampm:
                hora_24 = rec.hora_inicio_hora
                if rec.hora_inicio_ampm == 'PM' and hora_24 != 12:
                    hora_24 += 12
                elif rec.hora_inicio_ampm == 'AM' and hora_24 == 12:
                    hora_24 = 0
                rec.hora_inicio = hora_24
            else:
                rec.hora_inicio = 0.0

    def _inverse_hora_inicio(self):
        for rec in self:
            if rec.hora_inicio is not None:
                hora_24 = int(rec.hora_inicio)
                if hora_24 == 0:
                    rec.hora_inicio_hora = 12
                    rec.hora_inicio_ampm = 'AM'
                elif hora_24 < 12:
                    rec.hora_inicio_hora = hora_24
                    rec.hora_inicio_ampm = 'AM'
                elif hora_24 == 12:
                    rec.hora_inicio_hora = 12
                    rec.hora_inicio_ampm = 'PM'
                else:
                    rec.hora_inicio_hora = hora_24 - 12
                    rec.hora_inicio_ampm = 'PM'

    @api.depends('hora_fin_hora', 'hora_fin_ampm')
    def _compute_hora_fin(self):
        for rec in self:
            if rec.hora_fin_hora and rec.hora_fin_ampm:
                hora_24 = rec.hora_fin_hora
                if rec.hora_fin_ampm == 'PM' and hora_24 != 12:
                    hora_24 += 12
                elif rec.hora_fin_ampm == 'AM' and hora_24 == 12:
                    hora_24 = 0
                rec.hora_fin = hora_24
            else:
                rec.hora_fin = 0.0

    def _inverse_hora_fin(self):
        for rec in self:
            if rec.hora_fin is not None:
                hora_24 = int(rec.hora_fin)
                if hora_24 == 0:
                    rec.hora_fin_hora = 12
                    rec.hora_fin_ampm = 'AM'
                elif hora_24 < 12:
                    rec.hora_fin_hora = hora_24
                    rec.hora_fin_ampm = 'AM'
                elif hora_24 == 12:
                    rec.hora_fin_hora = 12
                    rec.hora_fin_ampm = 'PM'
                else:
                    rec.hora_fin_hora = hora_24 - 12
                    rec.hora_fin_ampm = 'PM'

    def action_marcar_ausencia(self):
        self.write({'state': 'cancelado'})
        return True

    def action_reprogramar(self):
        self.write({'state': 'programado'})
        return True
