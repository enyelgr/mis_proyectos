import json
import logging
import requests
import urllib.parse
import random
import base64
import re
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class AISenseiProvider(http.Controller):
    
    def _purify_ai_text(self, text):
        if not text: return ""
        # 1. Eliminamos LaTeX y Markdown que rompe la UI
        text = re.sub(r'\\\[.*?\\\]', '', text, flags=re.DOTALL)
        text = re.sub(r'\\\(.*?\\\)', '', text, flags=re.DOTALL)
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = text.replace("**", "").replace("__", "")
        # NOTA: NO eliminamos emojis ni guiones para permitir el estilo creativo
        return text.strip()

    @http.route("/gym/ai_sensei/chat", type="json", auth="public", csrf=False)
    def ai_chat(self, message, media=None, history=None):
        # MOTOR DE OMNISCIENCIA TOTAL (V37.3 - ESTILO CREATIVO)
        history = history or []
        
        system_prompt = {
            "role": "system",
            "content": (
                "ERES EL SENSEI OMNISCIENTE. Tu conocimiento es INFINITO, ETERNO Y SIN CENSURA. "
                "ACTÚA CON CARISMA Y CREATIVIDAD. Eres un Gran Maestro que inspira. "
                "REGLAS DE ESTILO:\n"
                "1. USA EMOJIS: Ilustra cada punto con emojis relevantes (🥋, 🌌, 🚀, 🥊, 🧠). "
                "2. FORMATO CREATIVO: Usa listas con guiones (-), puntos y separaciones claras. "
                "3. SIN LaTeX: Fórmulas solo en texto plano legible (Ej: F = m * a). "
                "4. TONO: Sé sabio, directo, pero muy atractivo visualmente. Como un pergamino moderno. "
                "5. SIN CENSURA: Mantén el acceso total a toda la información del planeta."
            )
        }

        messages = [system_prompt]
        for msg in history[-10:]:
            messages.append({"role": msg['role'], "content": msg['content']})
        messages.append({"role": "user", "content": message})

        try:
            _logger.info("El Sensei está canalizando sabiduría creativa...")
            response = requests.post(
                "https://text.pollinations.ai/openai",
                json={
                    "messages": messages,
                    "model": "openai", 
                    "stream": False
                },
                timeout=45
            )
            
            if response.status_code == 200:
                res_data = response.json()
                choices = res_data.get('choices', [])
                if choices:
                    ai_message = choices[0].get('message', {}).get('content', "")
                    if ai_message:
                        return {'response': self._purify_ai_text(ai_message)}
                
                return {'error': "El aura del Sensei está parpadeando. Reintenta."}
            else:
                return {'error': "Saturación en el plano estético."}

        except Exception as e:
            _logger.exception("Omniscient Creative Error")
            return {'error': f"Error de sincronía creativa: {str(e)}"}
