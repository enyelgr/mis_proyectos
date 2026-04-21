import json
import logging
import requests
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class AISenseiProvider(http.Controller):

    @http.route('/gym/ai_sensei/chat', type='json', auth='user', methods=['POST'])
    def ai_chat(self, message, history=None):
        params = request.env['ir.config_parameter'].sudo()
        api_key = params.get_param('horarios_clan_jiu_jitsu.gym_ai_api_key')

        if not api_key:
            return {
                'error': 'No hay Clave API configurada. Por favor, ve a Ajustes > Clan Jiu Jitsu y pega tu clave de OpenAI.',
                'response': 'Sensei está meditando off-line en este momento. (Falta configurar la API Key)'
            }

        history = history or []
        
        # System Prompt para darle personalidad de Sensei
        system_prompt = {
            "role": "system",
            "content": (
                "Eres el 'Sensei Virtual' del Dojo Clan Jiu Jitsu. "
                "Tu personalidad es sabia, disciplinada, alentadora pero firme, como un maestro de artes marciales. "
                "Respondes cualquier pregunta, pero siempre intentas relacionarla con los valores del guerrero, "
                "la disciplina o el Jiu Jitsu cuando sea apropiado. "
                "Si te preguntan sobre el gimnasio, asume que es una academia de alto nivel llamada Clan Jiu Jitsu."
            )
        }

        messages = [system_prompt]
        # Añadir historial para contexto
        for msg in history[-5:]: # Mantener solo los últimos 5 para ahorrar tokens
            messages.append({"role": msg['role'], "content": msg['content']})
        
        messages.append({"role": "user", "content": message})

        try:
            # Petición a OpenRouter (Bypassa bloqueos geográficos)
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://odoo.com", # Requerido por OpenRouter
                    "X-Title": "Odoo Dojo Sensei"        # Requerido por OpenRouter
                },
                json={
                    "model": "google/gemini-2.0-flash-lite-001", # Modelo rápido y potente
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 800
                },
                timeout=30
            )
            
            res_data = response.json()
            if response.status_code == 200:
                ai_message = res_data['choices'][0]['message']['content']
                return {'response': ai_message}
            else:
                error_msg = res_data.get('error', {}).get('message', 'Error desconocido de OpenRouter')
                _logger.error(f"AI Sensei API Error: {error_msg}")
                return {'error': f"Error de IA (OpenRouter): {error_msg}"}

        except Exception as e:
            _logger.exception("AI Sensei Connection Error")
            return {'error': f"Error de conexión: {str(e)}"}
