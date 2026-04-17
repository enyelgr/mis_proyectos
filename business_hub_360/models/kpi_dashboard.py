# business_hub_360/models/kpi_dashboard.py
from odoo import models, fields, api
from datetime import datetime, timedelta


class KPIDashboard(models.Model):
    _name = 'bh360.kpi.dashboard'
    _description = 'Dashboard de KPIs Empresariales'
    _rec_name = 'name'
    
    name = fields.Char(string='Nombre del Dashboard', required=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    
    # KPIs Financieros
    total_revenue = fields.Monetary(string='Ingresos Totales', compute='_compute_financial_kpis')
    total_expenses = fields.Monetary(string='Gastos Totales', compute='_compute_financial_kpis')
    net_profit = fields.Monetary(string='Beneficio Neto', compute='_compute_financial_kpis')
    cash_flow = fields.Monetary(string='Flujo de Caja', compute='_compute_financial_kpis')
    
    # KPIs de Inventario
    total_stock_value = fields.Monetary(string='Valor del Inventario', compute='_compute_inventory_kpis')
    low_stock_items = fields.Integer(string='Productos con Stock Bajo', compute='_compute_inventory_kpis')
    out_of_stock_items = fields.Integer(string='Productos Agotados', compute='_compute_inventory_kpis')
    
    # KPIs de Ventas
    total_sales = fields.Monetary(string='Ventas Totales', compute='_compute_sales_kpis')
    pending_quotes = fields.Integer(string='Presupuestos Pendientes', compute='_compute_sales_kpis')
    conversion_rate = fields.Float(string='Tasa de Conversión (%)', compute='_compute_sales_kpis')
    
    # KPIs de RRHH
    total_employees = fields.Integer(string='Total Empleados', compute='_compute_hr_kpis')
    employees_on_leave = fields.Integer(string='Empleados de Vacaciones', compute='_compute_hr_kpis')
    attendance_rate = fields.Float(string='Tasa de Asistencia (%)', compute='_compute_hr_kpis')
    
    # KPIs de Proyectos
    active_projects = fields.Integer(string='Proyectos Activos', compute='_compute_project_kpis')
    completed_projects = fields.Integer(string='Proyectos Completados', compute='_compute_project_kpis')
    project_budget_usage = fields.Float(string='Uso de Presupuesto (%)', compute='_compute_project_kpis')
    
    # Fecha de actualización
    last_updated = fields.Datetime(string='Última Actualización', default=fields.Datetime.now)
    
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id)
    
    @api.depends('company_id')
    def _compute_financial_kpis(self):
        for record in self:
            record.total_revenue = 0.0
            record.total_expenses = 0.0
            record.net_profit = 0.0
            record.cash_flow = 0.0
    
    @api.depends('company_id')
    def _compute_inventory_kpis(self):
        for record in self:
            record.total_stock_value = 0.0
            record.low_stock_items = 0
            record.out_of_stock_items = 0

    @api.depends('company_id')
    def _compute_sales_kpis(self):
        for record in self:
            record.total_sales = 0.0
            record.pending_quotes = 0
            record.conversion_rate = 0.0

    @api.depends('company_id')
    def _compute_hr_kpis(self):
        for record in self:
            record.total_employees = self.env['hr.employee'].search_count([])
            record.employees_on_leave = 0
            record.attendance_rate = 0.0

    @api.depends('company_id')
    def _compute_project_kpis(self):
        for record in self:
            record.active_projects = 0
            record.completed_projects = 0
            record.project_budget_usage = 0.0
    
    def action_refresh_dashboard(self):
        """Actualizar manualmente los KPIs"""
        self.last_updated = fields.Datetime.now()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
