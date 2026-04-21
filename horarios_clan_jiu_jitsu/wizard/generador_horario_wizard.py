from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta
from dateutil.relativedelta import relativedelta

class GymHorarioGeneradorWizard(models.TransientModel):
    _name = 'gym.horario.generador.wizard'
    _description = 'Asistente de Generación Masiva de Horarios'

    instructor_id = fields.Many2one('gym.instructor', string="Instructor", required=True)
    fecha_inicio = fields.Date(string="Fecha de Inicio", required=True, default=fields.Date.context_today)
    fecha_fin = fields.Date(string="Fecha de Fin", required=True, default=lambda self: fields.Date.context_today(self) + timedelta(days=6))
    
    # Configuración por días
    lunes_activo = fields.Boolean("Lunes", default=False)
    lunes_hora_inicio_str = fields.Selection(lambda self: self.env['gym.horario']._fields['hora_inicio_str'].selection, string="Hora Inicio Lunes")
    lunes_hora_fin_str = fields.Selection(lambda self: self.env['gym.horario']._fields['hora_fin_str'].selection, string="Hora Fin Lunes")
    lunes_area = fields.Selection([('1', 'Área 1'), ('2', 'Área 2'), ('3', 'Área 3'), ('4', 'Área 4')], string='Área Lunes')
    
    martes_activo = fields.Boolean("Martes", default=False)
    martes_hora_inicio_str = fields.Selection(lambda self: self.env['gym.horario']._fields['hora_inicio_str'].selection, string="Hora Inicio Martes")
    martes_hora_fin_str = fields.Selection(lambda self: self.env['gym.horario']._fields['hora_fin_str'].selection, string="Hora Fin Martes")
    martes_area = fields.Selection([('1', 'Área 1'), ('2', 'Área 2'), ('3', 'Área 3'), ('4', 'Área 4')], string='Área Martes')
    
    miercoles_activo = fields.Boolean("Miércoles", default=False)
    miercoles_hora_inicio_str = fields.Selection(lambda self: self.env['gym.horario']._fields['hora_inicio_str'].selection, string="Hora Inicio Miércoles")
    miercoles_hora_fin_str = fields.Selection(lambda self: self.env['gym.horario']._fields['hora_fin_str'].selection, string="Hora Fin Miércoles")
    miercoles_area = fields.Selection([('1', 'Área 1'), ('2', 'Área 2'), ('3', 'Área 3'), ('4', 'Área 4')], string='Área Miércoles')
    
    jueves_activo = fields.Boolean("Jueves", default=False)
    jueves_hora_inicio_str = fields.Selection(lambda self: self.env['gym.horario']._fields['hora_inicio_str'].selection, string="Hora Inicio Jueves")
    jueves_hora_fin_str = fields.Selection(lambda self: self.env['gym.horario']._fields['hora_fin_str'].selection, string="Hora Fin Jueves")
    jueves_area = fields.Selection([('1', 'Área 1'), ('2', 'Área 2'), ('3', 'Área 3'), ('4', 'Área 4')], string='Área Jueves')
    
    viernes_activo = fields.Boolean("Viernes", default=False)
    viernes_hora_inicio_str = fields.Selection(lambda self: self.env['gym.horario']._fields['hora_inicio_str'].selection, string="Hora Inicio Viernes")
    viernes_hora_fin_str = fields.Selection(lambda self: self.env['gym.horario']._fields['hora_fin_str'].selection, string="Hora Fin Viernes")
    viernes_area = fields.Selection([('1', 'Área 1'), ('2', 'Área 2'), ('3', 'Área 3'), ('4', 'Área 4')], string='Área Viernes')
    
    sabado_activo = fields.Boolean("Sábado", default=False)
    sabado_hora_inicio_str = fields.Selection(lambda self: self.env['gym.horario']._fields['hora_inicio_str'].selection, string="Hora Inicio Sábado")
    sabado_hora_fin_str = fields.Selection(lambda self: self.env['gym.horario']._fields['hora_fin_str'].selection, string="Hora Fin Sábado")
    sabado_area = fields.Selection([('1', 'Área 1'), ('2', 'Área 2'), ('3', 'Área 3'), ('4', 'Área 4')], string='Área Sábado')
    
    domingo_activo = fields.Boolean("Domingo", default=False)
    domingo_hora_inicio_str = fields.Selection(lambda self: self.env['gym.horario']._fields['hora_inicio_str'].selection, string="Hora Inicio Domingo")
    domingo_hora_fin_str = fields.Selection(lambda self: self.env['gym.horario']._fields['hora_fin_str'].selection, string="Hora Fin Domingo")
    domingo_area = fields.Selection([('1', 'Área 1'), ('2', 'Área 2'), ('3', 'Área 3'), ('4', 'Área 4')], string='Área Domingo')

    @api.onchange('lunes_hora_inicio_str', 'martes_hora_inicio_str', 'miercoles_hora_inicio_str', 'jueves_hora_inicio_str', 'viernes_hora_inicio_str', 'sabado_hora_inicio_str', 'domingo_hora_inicio_str')
    def _onchange_any_hora_inicio_str(self):
        # Auto-compute rule for each active day
        days = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        for day in days:
            start_val = getattr(self, f'{day}_hora_inicio_str')
            if start_val:
                try:
                    new_val = float(start_val) + 1.0
                    if new_val <= 21.0:
                        setattr(self, f'{day}_hora_fin_str', str(new_val))
                except:
                    pass

    def action_generar_horarios(self):
        self.ensure_one()
        if self.fecha_inicio > self.fecha_fin:
            raise UserError("La Fecha Final no puede ser menor a la Fecha de Inicio.")
            
        any_day_active = any([self.lunes_activo, self.martes_activo, self.miercoles_activo, 
                             self.jueves_activo, self.viernes_activo, self.sabado_activo, self.domingo_activo])
        if not any_day_active:
            raise UserError("Debes activar al menos un día de la semana para generar las clases.")
        
        day_mapping = {
            0: (self.lunes_activo, self.lunes_hora_inicio_str, self.lunes_hora_fin_str, self.lunes_area),
            1: (self.martes_activo, self.martes_hora_inicio_str, self.martes_hora_fin_str, self.martes_area),
            2: (self.miercoles_activo, self.miercoles_hora_inicio_str, self.miercoles_hora_fin_str, self.miercoles_area),
            3: (self.jueves_activo, self.jueves_hora_inicio_str, self.jueves_hora_fin_str, self.jueves_area),
            4: (self.viernes_activo, self.viernes_hora_inicio_str, self.viernes_hora_fin_str, self.viernes_area),
            5: (self.sabado_activo, self.sabado_hora_inicio_str, self.sabado_hora_fin_str, self.sabado_area),
            6: (self.domingo_activo, self.domingo_hora_inicio_str, self.domingo_hora_fin_str, self.domingo_area),
        }
        
        horario_env = self.env['gym.horario']
        horarios_creados = 0
        horarios_chocan = 0
        current_date = self.fecha_inicio
        
        while current_date <= self.fecha_fin:
            weekday = current_date.weekday()
            is_active, h_in, h_end, area_doc = day_mapping[weekday]
            
            if is_active:
                if not area_doc or not h_in or not h_end:
                    raise UserError(f"Activaste un día pero olvidaste asignarle su Hora o Área.")
                    
                domain = [
                    ('area', '=', area_doc),
                    ('fecha', '=', current_date),
                    ('state', '!=', 'cancelado'),
                    ('hora_inicio', '<', float(h_end)),
                    ('hora_fin', '>', float(h_in)),
                ]
                conflict = horario_env.search(domain, limit=1)
                
                if not conflict:
                    horario_env.create({
                        'instructor_id': self.instructor_id.id,
                        'fecha': current_date,
                        'hora_inicio': float(h_in),
                        'hora_fin': float(h_end),
                        'area': area_doc,
                        'state': 'programado'
                    })
                    horarios_creados += 1
                else:
                    horarios_chocan += 1
            
            current_date += timedelta(days=1)
            
        success_msg = f"✅ Se han programado exitosamente {horarios_creados} clases en el calendario de este Instructor."
        if horarios_chocan > 0:
            success_msg += f"\n\n❌ {horarios_chocan} clases fueron ignoradas porque el Área estaba ocupada en esa hora por otra actividad."
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Generación Completada',
                'message': success_msg,
                'type': 'success' if horarios_creados > 0 else 'warning',
                'sticky': True,
            }
        }
