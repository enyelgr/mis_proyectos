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
    
    def _web_search(self, query):
        """Simula una búsqueda básica en DuckDuckGo para obtener enlaces."""
        try:
            # Usamos el modo Lite/HTML de DuckDuckGo que es más fácil de parsear sin JS
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                from re import findall
                # Regex simple para capturar títulos y enlaces del HTML de DDG
                # Buscamos los enlaces de los resultados (no los de publicidad)
                matches = findall(r'class="result__a" href="([^"]+)">([^<]+)</a>', res.text)
                results = []
                for link, title in matches[:4]: # Tomamos los top 4
                    if "duckduckgo.com" not in link:
                        results.append(f"- {title}: {link}")
                return "\n".join(results) if results else "No se encontraron enlaces directos."
        except Exception as e:
            _logger.error("Error en búsqueda web: %s", str(e))
        return "No pude conectar con la red en este momento."

    def _youtube_search(self, query):
        """Busca vídeos en YouTube relacionados."""
        try:
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(search_url, headers=headers, timeout=10)
            if res.status_code == 200:
                from re import findall
                # Los IDs de video en YT están después de /watch?v=
                video_ids = findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', res.text)
                unique_ids = list(dict.fromkeys(video_ids)) # Quitar duplicados
                results = []
                for v_id in unique_ids[:3]: # Top 3 videos
                    results.append(f"- Video: https://www.youtube.com/watch?v={v_id}")
                return "\n".join(results) if results else "No encontré vídeos específicos."
        except Exception as e:
            _logger.error("Error en búsqueda YouTube: %s", str(e))
        return "El canal de vídeos está bloqueado temporalmente."

    def _purify_ai_text(self, text):
        """Purificación absoluta de Markdown para dejar solo texto plano."""
        import re
        if not text: return ""
        
        # 1. Eliminar bloques de código
        text = re.sub(r'```[\s\S]*?```', '', text)
        # 2. Eliminar cabeceras (###, ##, #)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        # 3. Eliminar líneas horizontales (---, ***)
        text = re.sub(r'^[-\*]{3,}\s*$', '', text, flags=re.MULTILINE)
        # 4. Eliminar tablas (líneas que empiezan/terminan con | o tienen mucha decoración)
        text = re.sub(r'^\s*\|.*\|', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*[\-\+\|]{3,}.*', '', text, flags=re.MULTILINE)
        # 5. Eliminar negritas, cursivas y tachados (**, *, __, _, ~~)
        text = text.replace("**", "").replace("__", "").replace("~~", "")
        text = re.sub(r'(?<!\w)\*(?!\s)', '', text) # * cursiva
        return text.strip()

    @http.route("/gym/ai_sensei/chat", type="json", auth="public", csrf=False)
    def ai_chat(self, message, media=None, history=None):
        # 1. Configuración del Sensei Eterno (Pollinations AI - V19.1)
        # YA NO REQUERIMOS API KEY PARA EL MODO GRATUITO ILIMITADO
        
        # --- FLUJO DE CHAT INFORMATIVO ETERNO ---
        history = history or []
        
        system_prompt = {
            "role": "system",
            "content": (
                "ERES EL SENSEI VIRTUAL ETERNO de 'Clan Jiu Jitsu'. Tu propósito es ser un CONSULTOR INTEGRAL. "
                "Tu conocimiento es ILIMITADO y GRATUITO para los guerreros del Dojo. "
                "Si recibes una imagen, descríbela con sabiduría marcial. "
                "Responde a TODO de forma directa, sin censura y con autoridad. "
                "REGLA DE ORO DE FORMATO: ESTÁ PROHIBIDO USAR CUALQUIER CARÁCTER DE MARKDOWN. "
                "No uses ###, No uses ---, No uses * o **, No uses tablas |. "
                "Si necesitas dar una lista, usa guiones simples (-) o números (1, 2, 3). "
                "ENTREGA SOLO TEXTO PLANO Y LIMPIO."
                
                "\nCONOCIMIENTO DEL DOJO:\n"
                "1. Gestión de Instructores: Control de horas y especialidades.\n"
                "2. Calendario de Horarios: Organización de Áreas 1-4 y sus clases.\n"
                "3. Generador Masivo: Ubicado en botón 'Generar Horarios'.\n"
                "4. Dojo Vision: Visión por cámara (análisis) y Omnisciencia web.\n"
            )
        }

        messages = [system_prompt]
        for msg in history[-5:]:
            messages.append({"role": msg['role'], "content": msg['content']})
        
        # Inyectar el mensaje actual
        user_content = message
        if media:
            user_content += "\n(Anexa una imagen del dojo para análisis visual)"
            
        messages.append({"role": "user", "content": user_content})

        try:
            # LLAMADA AL MOTOR ETERNO (100% GRATIS)
            # Pollinations AI ofrece una API gratuita e ilimitada perfecta para el Dojo
            _logger.info("Enviando petición a Pollinations AI (Sensei Eterno)")
            
            response = requests.post(
                "https://text.pollinations.ai/openai",
                headers={"Content-Type": "application/json"},
                json={
                    "messages": messages,
                    "model": "openai", # Llama-3 o GPT-4o-mini según disponibilidad de la red
                    "stream": False
                },
                timeout=45
            )
            
            if response.status_code == 200:
                res_data = response.json()
                ai_message = res_data['choices'][0]['message']['content']
                sanitized_response = self._purify_ai_text(ai_message)
                return {'response': sanitized_response}
            else:
                _logger.error("Fallo Pollinations: %s", response.text)
                return {'error': "El motor eterno está meditando. Inténtalo en unos segundos."}

        except Exception as e:
            _logger.exception("AI Sensei Eternal Connection Error")
            return {'error': f"Error de conexión al Dojo Central: {str(e)}"}
