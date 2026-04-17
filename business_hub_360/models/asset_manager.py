# business_hub_360/models/asset_manager.py
from odoo import models, fields, api
from datetime import datetime, timedelta


class AssetCategory(models.Model):
    _name = 'bh360.asset.category'
    _description = 'Categoría de Activos'
    
    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', required=True)

    depreciation_method = fields.Selection([
        ('straight_line', 'Línea Recta'),
        ('declining_balance', 'Saldo Decreciente'),
        ('units_of_production', 'Unidades de Producción'),
    ], string='Método de Depreciación', default='straight_line')

    depreciation_years = fields.Float(string='Años de Depreciación', default=5)
    salvage_value_percent = fields.Float(string='Valor Residual (%)', default=10.0)
    
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)


class FixedAsset(models.Model):
    _name = 'bh360.fixed.asset'
    _description = 'Activo Fijo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'purchase_date desc'
    
    name = fields.Char(string='Nombre del Activo', required=True)
    asset_code = fields.Char(string='Código', copy=False, readonly=True, default='Nuevo')
    
    category_id = fields.Many2one('bh360.asset.category', string='Categoría', required=True)
    
    asset_type = fields.Selection([
        ('equipment', 'Equipo'),
        ('vehicle', 'Vehículo'),
        ('machinery', 'Maquinaria'),
        ('furniture', 'Mobiliario'),
        ('building', 'Edificio'),
        ('it_hardware', 'Hardware IT'),
        ('other', 'Otro'),
    ], string='Tipo de Activo', required=True)

    purchase_value = fields.Monetary(string='Valor de Compra', required=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id)
    
    purchase_date = fields.Date(string='Fecha de Compra', required=True)
    warranty_date = fields.Date(string='Fin de Garantía')

    supplier_id = fields.Many2one('res.partner', string='Proveedor')
    invoice_number = fields.Char(string='Número de Factura')
    
    current_value = fields.Monetary(string='Valor Actual', compute='_compute_depreciation')
    accumulated_depreciation = fields.Monetary(string='Depreciación Acumulada', compute='_compute_depreciation')
    
    location_id = fields.Many2one('stock.location', string='Ubicación')
    responsible_id = fields.Many2one('hr.employee', string='Responsable')
    
    status = fields.Selection([
        ('draft', 'Borrador'),
        ('active', 'En Uso'),
        ('maintenance', 'En Mantenimiento'),
        ('inactive', 'Inactivo'),
        ('disposed', 'Dado de Baja'),
    ], string='Estado', default='draft', tracking=True)

    barcode = fields.Char(string='Código de Barras', copy=False)
    notes = fields.Text(string='Notas')
    attachment_ids = fields.Many2many('ir.attachment', string='Adjuntos')
    
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    
    @api.model
    def create(self, vals):
        if vals.get('asset_code', 'Nuevo') == 'Nuevo':
            vals['asset_code'] = self.env['ir.sequence'].next_by_code('bh360.fixed.asset') or 'Nuevo'
        return super().create(vals)
    
    @api.depends('purchase_value', 'purchase_date', 'category_id')
    def _compute_depreciation(self):
        for asset in self:
            if asset.purchase_date and asset.category_id:
                years = asset.category_id.depreciation_years
                salvage_percent = asset.category_id.salvage_value_percent
                
                salvage_value = asset.purchase_value * (salvage_percent / 100)
                depreciable_value = asset.purchase_value - salvage_value

                annual_depreciation = depreciable_value / years if years > 0 else 0
                
                days_owned = (fields.Date.today() - asset.purchase_date).days
                years_owned = days_owned / 365.0
                
                accumulated = min(annual_depreciation * years_owned, depreciable_value)
                current = asset.purchase_value - accumulated

                asset.accumulated_depreciation = accumulated
                asset.current_value = current
            else:
                asset.accumulated_depreciation = 0.0
                asset.current_value = asset.purchase_value
    
    def action_activate(self):
        self.status = 'active'

    def action_maintenance(self):
        self.status = 'maintenance'
    
    def action_dispose(self):
        self.status = 'disposed'
