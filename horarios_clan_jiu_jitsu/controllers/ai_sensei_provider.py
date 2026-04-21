import json
import logging
import requests
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class AISenseiProvider(http.Controller):

    @http.route('/gym/ai_sensei/chat', type='json', auth='user', methods=['POST'])
    def ai_chat(self, message, media=None, history=None):
        params = request.env['ir.config_parameter'].sudo()
        api_key = params.get_param('horarios_clan_jiu_jitsu.gym_ai_api_key')

        if not api_key:
            return {
                'error': 'No hay Clave API configurada.',
                'response': 'Sensei está offline. (Falta API Key)'
            }

        history = history or []
        
        system_prompt = {
            "role": "system",
            "content": (
                "Eres el 'Sensei Virtual' del Dojo Clan Jiu Jitsu. "
                "Tu personalidad es sabia, disciplinada y firme. "
                "Si recibes una imagen, actúa como si estuvieras viendo al alumno en tiempo real. "
                "Analiza su postura, el dojo o cualquier detalle visual para dar consejos de mejora."
            )
        }

        messages = [system_prompt]
        for msg in history[-5:]:
            messages.append({"role": msg['role'], "content": msg['content']})
        
        # Construir contenido multimodal si hay imagen
        user_content = [{"type": "text", "text": message}]
        if media:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": media # media ya viene como data:image/jpeg;base64,...
                }
            })

        messages.append({"role": "user", "content": user_content})

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://odoo.com",
                    "X-Title": "Odoo Dojo Sensei Live"
                },
                json={
                    "model": "google/gemini-2.0-flash-lite-001",
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
                error_msg = res_data.get('error', {}).get('message', 'Error de OpenRouter')
                return {'error': f"IA Error: {error_msg}"}

        except Exception as e:
            return {'error': f"Conexión Error: {str(e)}"}

        except Exception as e:
            _logger.exception("AI Sensei Connection Error")
            return {'error': f"Error de conexión: {str(e)}"}
