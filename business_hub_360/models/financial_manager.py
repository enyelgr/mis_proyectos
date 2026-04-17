# business_hub_360/models/financial_manager.py
from odoo import models, fields, api
from datetime import datetime, timedelta


class FinancialTransaction(models.Model):
    _name = 'bh360.financial.transaction'
    _description = 'Transacción Financiera'
    _order = 'date desc'

    name = fields.Char(string='Referencia', required=True, copy=False, readonly=True, default='Nuevo')
    transaction_type = fields.Selection([
        ('income', 'Ingreso'),
        ('expense', 'Gasto'),
        ('transfer', 'Transferencia'),
    ], string='Tipo de Transacción', required=True)

    amount = fields.Monetary(string='Monto', required=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id)
    
    date = fields.Date(string='Fecha', required=True, default=fields.Date.context_today)
    description = fields.Text(string='Descripción')

    category_id = fields.Many2one('bh360.financial.category', string='Categoría')
    partner_id = fields.Many2one('res.partner', string='Tercero')
    
    account_id = fields.Many2one('account.account', string='Cuenta Contable')
    journal_id = fields.Many2one('account.journal', string='Diario')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('pending', 'Pendiente Aprobación'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('posted', 'Contabilizado'),
    ], string='Estado', default='draft', tracking=True)

    approved_by = fields.Many2one('res.users', string='Aprobado Por')
    approved_date = fields.Datetime(string='Fecha de Aprobación')
    
    attachment_ids = fields.Many2many('ir.attachment', string='Archivos Adjuntos')

    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('bh360.financial.transaction') or 'Nuevo'
        return super().create(vals)

    def action_submit_for_approval(self):
        self.state = 'pending'
    
    def action_approve(self):
        self.state = 'approved'
        self.approved_by = self.env.uid
        self.approved_date = fields.Datetime.now()

    def action_reject(self):
        self.state = 'rejected'
    
    def action_post(self):
        self.state = 'posted'

class FinancialCategory(models.Model):
    _name = 'bh360.financial.category'
    _description = 'Categoría Financiera'
    
    name = fields.Char(string='Nombre', required=True)
    type = fields.Selection([
        ('income', 'Ingreso'),
        ('expense', 'Gasto'),
    ], string='Tipo', required=True)

    parent_id = fields.Many2one('bh360.financial.category', string='Categoría Padre')
    child_ids = fields.One2many('bh360.financial.category', 'parent_id', string='Subcategorías')
    
    color = fields.Integer(string='Color')
    active = fields.Boolean(default=True)
    
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
