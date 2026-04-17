# business_hub_360/models/support_tickets.py
from odoo import models, fields, api
from datetime import datetime, timedelta


class SupportTicket(models.Model):
    _name = 'bh360.support.ticket'
    _description = 'Ticket de Soporte'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'

    name = fields.Char(string='Número de Ticket', copy=False, readonly=True, default='Nuevo')
    
    subject = fields.Char(string='Asunto', required=True)
    description = fields.Html(string='Descripción', required=True)
    
    partner_id = fields.Many2one('res.partner', string='Cliente')
    
    category_id = fields.Many2one('bh360.support.category', string='Categoría', required=True)
    
    priority = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ], string='Prioridad', default='medium', tracking=True)
    
    stage_id = fields.Many2one('bh360.support.stage', string='Etapa', tracking=True)
    
    assigned_to = fields.Many2one('res.users', string='Asignado A')

    opening_date = fields.Datetime(string='Fecha de Apertura', default=fields.Datetime.now)
    closing_date = fields.Datetime(string='Fecha de Cierre')
    deadline_date = fields.Datetime(string='Fecha Límite', compute='_compute_deadline')

    state = fields.Selection([
        ('new', 'Nuevo'),
        ('in_progress', 'En Progreso'),
        ('waiting_customer', 'Esperando Cliente'),
        ('resolved', 'Resuelto'),
        ('closed', 'Cerrado'),
    ], string='Estado', default='new', tracking=True)

    satisfaction_rating = fields.Selection([
        ('1', '1 - Muy Insatisfecho'),
        ('2', '2 - Insatisfecho'),
        ('3', '3 - Neutral'),
        ('4', '4 - Satisfecho'),
        ('5', '5 - Muy Satisfecho'),
    ], string='Satisfacción')

    satisfaction_comment = fields.Text(string='Comentario de Satisfacción')

    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('bh360.support.ticket') or 'Nuevo'
        return super().create(vals)

    @api.depends('priority', 'opening_date')
    def _compute_deadline(self):
        for ticket in self:
            priority_hours = {
                'low': 72,
                'medium': 48,
                'high': 24,
                'critical': 4,
            }
            hours = priority_hours.get(ticket.priority, 48)
            ticket.deadline_date = ticket.opening_date + timedelta(hours=hours)

    def action_start_progress(self):
        self.state = 'in_progress'
    
    def action_resolve(self):
        self.state = 'resolved'
        self.closing_date = fields.Datetime.now()
    
    def action_close(self):
        self.state = 'closed'

class SupportCategory(models.Model):
    _name = 'bh360.support.category'
    _description = 'Categoría de Soporte'
    
    name = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(default=True)

class SupportStage(models.Model):
    _name = 'bh360.support.stage'
    _description = 'Etapa de Ticket'
    _order = 'sequence'
    
    name = fields.Char(string='Nombre', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    fold = fields.Boolean(string='Plegado en Kanban')
    is_closed = fields.Boolean(string='Es Cierre')
