# business_hub_360/models/document_manager.py
from odoo import models, fields, api
from datetime import datetime, timedelta


class DocumentCategory(models.Model):
    _name = 'bh360.document.category'
    _description = 'Categoría de Documentos'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    parent_id = fields.Many2one('bh360.document.category', string='Categoría Padre')
    child_ids = fields.One2many('bh360.document.category', 'parent_id', string='Subcategorías')
    
    allowed_groups = fields.Many2many('res.groups', string='Grupos Permitidos')
    retention_days = fields.Integer(string='Días de Retención')
    
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)


class BusinessDocument(models.Model):
    _name = 'bh360.document'
    _description = 'Documento Empresarial'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    name = fields.Char(string='Nombre del Documento', required=True)
    document_number = fields.Char(string='Número', copy=False, readonly=True, default='Nuevo')
    
    category_id = fields.Many2one('bh360.document.category', string='Categoría', required=True)
    
    document_file = fields.Binary(string='Archivo', required=True, attachment=True)
    document_filename = fields.Char(string='Nombre de Archivo')

    document_type = fields.Selection([
        ('pdf', 'PDF'),
        ('doc', 'Word'),
        ('xls', 'Excel'),
        ('img', 'Imagen'),
        ('other', 'Otro'),
    ], string='Tipo', compute='_compute_document_type', store=True)
    
    description = fields.Text(string='Descripción')
    
    tags = fields.Many2many('bh360.document.tag', string='Etiquetas')
    
    owner_id = fields.Many2one('res.users', string='Propietario', default=lambda self: self.env.uid)
    authorized_users = fields.Many2many('res.users', string='Usuarios Autorizados')

    status = fields.Selection([
        ('draft', 'Borrador'),
        ('active', 'Activo'),
        ('archived', 'Archivado'),
        ('expired', 'Vencido'),
    ], string='Estado', default='draft', tracking=True)
    
    issue_date = fields.Date(string='Fecha de Emisión')
    expiry_date = fields.Date(string='Fecha de Vencimiento')

    version = fields.Char(string='Versión', default='1.0')
    
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    
    @api.model
    def create(self, vals):
        if vals.get('document_number', 'Nuevo') == 'Nuevo':
            vals['document_number'] = self.env['ir.sequence'].next_by_code('bh360.document') or 'Nuevo'
        return super().create(vals)

    @api.depends('document_filename')
    def _compute_document_type(self):
        for record in self:
            if record.document_filename:
                ext = record.document_filename.split('.')[-1].lower()
                if ext == 'pdf':
                    record.document_type = 'pdf'
                elif ext in ['doc', 'docx']:
                    record.document_type = 'doc'
                elif ext in ['xls', 'xlsx', 'csv']:
                    record.document_type = 'xls'
                elif ext in ['jpg', 'jpeg', 'png', 'gif']:
                    record.document_type = 'img'
                else:
                    record.document_type = 'other'
            else:
                record.document_type = 'other'

    def action_activate(self):
        self.status = 'active'
    
    def action_archive(self):
        self.status = 'archived'


class DocumentTag(models.Model):
    _name = 'bh360.document.tag'
    _description = 'Etiqueta de Documento'

    name = fields.Char(string='Nombre', required=True)
    color = fields.Integer(string='Color')
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)

