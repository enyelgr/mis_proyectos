# business_hub_360/models/inventory_pro.py
from odoo import models, fields, api
from datetime import datetime, timedelta


class InventoryAlert(models.Model):
    _name = 'bh360.inventory.alert'
    _description = 'Alerta de Inventario'
    _order = 'priority desc, date desc'

    name = fields.Char(string='Referencia', required=True, copy=False, readonly=True, default='Nuevo')
    product_id = fields.Many2one('product.template', string='Producto', required=True)

    alert_type = fields.Selection([
        ('low_stock', 'Stock Bajo'),
        ('out_of_stock', 'Agotado'),
        ('expiring_soon', 'Próximo a Vencer'),
        ('overstock', 'Exceso de Stock'),
    ], string='Tipo de Alerta', required=True)

    current_quantity = fields.Float(string='Cantidad Actual')
    minimum_quantity = fields.Float(string='Cantidad Mínima')
    maximum_quantity = fields.Float(string='Cantidad Máxima')

    priority = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ], string='Prioridad', default='medium')

    state = fields.Selection([
        ('new', 'Nueva'),
        ('in_progress', 'En Progreso'),
        ('resolved', 'Resuelta'),
        ('ignored', 'Ignorada'),
    ], string='Estado', default='new')

    date = fields.Datetime(string='Fecha', default=fields.Datetime.now)
    resolved_date = fields.Datetime(string='Fecha de Resolución')
    resolved_by = fields.Many2one('res.users', string='Resuelto Por')

    notes = fields.Text(string='Notas')
    action_taken = fields.Text(string='Acción Tomada')
    
    warehouse_id = fields.Many2one('stock.warehouse', string='Almacén')
    location_id = fields.Many2one('stock.location', string='Ubicación')
    
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('bh360.inventory.alert') or 'Nuevo'
        return super().create(vals)
    
    def action_resolve(self):
        self.state = 'resolved'
        self.resolved_date = fields.Datetime.now()
        self.resolved_by = self.env.uid
    
    def action_ignore(self):
        self.state = 'ignored'
