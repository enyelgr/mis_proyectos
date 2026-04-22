from datetime import datetime, timedelta, time
import pytz

from odoo import models, fields, api
from odoo.exceptions import ValidationError

TIME_SLOTS = [
    ('6.0', '06:00 AM'), ('6.5', '06:30 AM'),
    ('7.0', '07:00 AM'), ('7.5', '07:30 AM'),
    ('8.0', '08:00 AM'), ('8.5', '08:30 AM'),
    ('9.0', '09:00 AM'), ('9.5', '09:30 AM'),
    ('10.0', '10:00 AM'), ('10.5', '10:30 AM'),
    ('11.0', '11:00 AM'), ('11.5', '11:30 AM'),
    ('12.0', '12:00 PM'), ('12.5', '12:30 PM'),
    ('13.0', '01:00 PM'), ('13.5', '01:30 PM'),
    ('14.0', '02:00 PM'), ('14.5', '02:30 PM'),
    ('15.0', '03:00 PM'), ('15.5', '03:30 PM'),
    ('16.0', '04:00 PM'), ('16.5', '04:30 PM'),
    ('17.0', '05:00 PM'), ('17.5', '05:30 PM'),
    ('18.0', '06:00 PM'), ('18.5', '06:30 PM'),
    ('19.0', '07:00 PM'), ('19.5', '07:30 PM'),
    ('20.0', '08:00 PM'), ('20.5', '08:30 PM'),
    ('21.0', '09:00 PM')
]


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
    hora_inicio = fields.Float(string='Hora Inicio', required=True, default=9.0)
    hora_fin = fields.Float(string='Hora Fin', required=True, default=10.0)
    hora_inicio_str = fields.Char(string="Hora Inicio (AM/PM)", compute='_compute_horas_str', store=True)
    hora_fin_str = fields.Char(string="Hora Fin (AM/PM)", compute='_compute_horas_str', store=True)
    top_position = fields.Float(string='Posición vertical', compute='_compute_schedule_layout', store=True)
    block_height = fields.Float(string='Altura del bloque', compute='_compute_schedule_layout', store=True)
    duration = fields.Float(string='Duración (hrs)', compute='_compute_duration', store=True)
    area = fields.Selection([
        ('1', 'Área 1'),
        ('2', 'Área 2'),
        ('3', 'Área 3'),
        ('4', 'Área 4'),
    ], string='Área', required=True, default='1')
    instructor_id = fields.Many2one('gym.instructor', string='Instructor', required=True)
    instructor_especialidad = fields.Char(string='Especialidad', related='instructor_id.especialidad', store=True)
    state = fields.Selection([
        ('programado', 'Programado'),
        ('cancelado', 'Cancelado / Ausencia'),
        ('completado', 'Completado'),
    ], string='Estado', default='programado', tracking=True)

    @api.depends('fecha', 'hora_inicio', 'hora_fin')
    def _compute_datetime(self):
        user_tz_name = self._context.get('tz') or self.env.user.tz or 'UTC'
        try:
            user_tz = pytz.timezone(user_tz_name)
        except pytz.UnknownTimeZoneError:
            user_tz = pytz.utc
            
        for rec in self:
            if rec.fecha_hora_inicio and rec.fecha_hora_fin:
                continue # No sobrescribir si ya viene manual
            if rec.fecha and rec.hora_inicio is not None and rec.hora_fin is not None:
                h_start, m_start = int(rec.hora_inicio % 24), int((rec.hora_inicio % 1) * 60)
                h_fin, m_fin = int(rec.hora_fin), int((rec.hora_fin % 1) * 60)
                
                # Manejo de hora >= 24 (Medianoche) para evitar ValueError
                if h_fin >= 24:
                    h_fin = 23
                    m_fin = 59
                
                dt_start = datetime.combine(rec.fecha, time(hour=h_start, minute=m_start))
                dt_fin = datetime.combine(rec.fecha, time(hour=h_fin, minute=m_fin))
                
                rec.fecha_hora_inicio = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)
                rec.fecha_hora_fin = user_tz.localize(dt_fin).astimezone(pytz.utc).replace(tzinfo=None)
            else:
                rec.fecha_hora_inicio = False
                rec.fecha_hora_fin = False

    def _inverse_datetime(self):
        user_tz_name = self._context.get('tz') or self.env.user.tz or 'UTC'
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

    @api.depends('hora_inicio', 'hora_fin')
    def _compute_horas_str(self):
        for rec in self:
            rec.hora_inicio_str = self._format_12h(rec.hora_inicio)
            rec.hora_fin_str = self._format_12h(rec.hora_fin)

    def _format_12h(self, float_time):
        if float_time is None: return False
        h = int(float_time)
        m = int((float_time % 1) * 60)
        meridiem = "AM" if h < 12 else "PM"
        h_12 = h if h <= 12 else h - 12
        if h_12 == 0: h_12 = 12
        return f"{h_12:02d}:{m:02d} {meridiem}"

    def _inverse_horas_str(self):
        for rec in self:
            if rec.hora_inicio_str:
                rec.hora_inicio = float(rec.hora_inicio_str)
            if rec.hora_fin_str:
                rec.hora_fin = float(rec.hora_fin_str)

    @api.onchange('hora_inicio_str')
    def _onchange_hora_inicio_str(self):
        if self.hora_inicio_str:
            val = float(self.hora_inicio_str)
            new_val = val + 1.0 # Default rule: 1 hour class
            if new_val <= 21.0:
                self.hora_fin_str = str(new_val)

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
            if rec.dia_semana:
                continue # Respetar inyección manual
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

    @api.depends('instructor_id', 'instructor_especialidad')
    def _compute_name(self):
        for rec in self:
            if rec.instructor_id:
                disc = (rec.instructor_especialidad or 'CLASE').upper()
                name = rec.instructor_id.name.upper()
                rec.name = f"{disc} | {name}"
            else:
                rec.name = 'HORARIO DISPONIBLE'

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


    def action_marcar_ausencia(self):
        self.write({'state': 'cancelado'})
        return True

    def action_reprogramar(self):
        self.write({'state': 'programado'})
        return True
