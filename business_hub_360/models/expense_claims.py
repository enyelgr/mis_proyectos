# business_hub_360/models/expense_claims.py
from odoo import models, fields, api
from datetime import datetime, timedelta


class ExpenseClaim(models.Model):
    _name = 'bh360.expense.claim'
    _description = 'Reclamación de Gastos'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'claim_date desc'

    name = fields.Char(string='Referencia', copy=False, readonly=True, default='Nuevo')
    
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True, default=lambda self: self.env.user.employee_ids[:1])
    user_id = fields.Many2one('res.users', related='employee_id.user_id', store=True)
    
    claim_date = fields.Date(string='Fecha de Reclamación', default=fields.Date.context_today)
    period_start = fields.Date(string='Periodo Inicio', required=True)
    period_end = fields.Date(string='Periodo Fin', required=True)
    
    line_ids = fields.One2many('bh360.expense.claim.line', 'claim_id', string='Líneas de Gasto')
    
    total_amount = fields.Monetary(string='Total', compute='_compute_total', store=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id)
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('submitted', 'Enviado'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('paid', 'Pagado'),
    ], string='Estado', default='draft', tracking=True)

    approved_by = fields.Many2one('res.users', string='Aprobado Por')
    approved_date = fields.Datetime(string='Fecha de Aprobación')
    paid_date = fields.Date(string='Fecha de Pago')

    attachment_ids = fields.Many2many('ir.attachment', string='Comprobantes', required=True)
    notes = fields.Text(string='Notas')
    
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('bh360.expense.claim') or 'Nuevo'
        return super().create(vals)

    @api.depends('line_ids.amount')
    def _compute_total(self):
        for claim in self:
            claim.total_amount = sum(line.amount for line in claim.line_ids)
    
    def action_submit(self):
        self.state = 'submitted'

    def action_approve(self):
        self.state = 'approved'
        self.approved_by = self.env.uid
        self.approved_date = fields.Datetime.now()
    
    def action_reject(self):
        self.state = 'rejected'

    def action_pay(self):
        self.state = 'paid'
        self.paid_date = fields.Date.today()


class ExpenseClaimLine(models.Model):
    _name = 'bh360.expense.claim.line'
    _description = 'Línea de Gasto'
    _order = 'date desc'

    claim_id = fields.Many2one('bh360.expense.claim', string='Reclamación', required=True, ondelete='cascade')
    
    date = fields.Date(string='Fecha del Gasto', required=True)
    category_id = fields.Many2one('bh360.expense.category', string='Categoría', required=True)
    
    description = fields.Char(string='Descripción', required=True)
    amount = fields.Monetary(string='Monto', required=True)
    currency_id = fields.Many2one('res.currency', related='claim_id.currency_id')
    
    payment_mode = fields.Selection([
        ('company_card', 'Tarjeta de Empresa'),
        ('personal_cash', 'Efectivo Personal'),
        ('personal_card', 'Tarjeta Personal'),
    ], string='Modo de Pago', required=True)

    receipt_image = fields.Binary(string='Comprobante', attachment=True)
    
    company_id = fields.Many2one('res.company', related='claim_id.company_id', store=True)


class ExpenseCategory(models.Model):
    _name = 'bh360.expense.category'
    _description = 'Categoría de Gastos'
    
    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', required=True)

    requires_receipt = fields.Boolean(string='Requiere Comprobante', default=True)
    
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
