from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    gym_ai_api_key = fields.Char(
        string='Clave API de IA (OpenAI/Gemini)',
        config_parameter='horarios_clan_jiu_jitsu.gym_ai_api_key',
        help="Pega aquí tu clave de API para activar el Sensei Interactivo."
    )
