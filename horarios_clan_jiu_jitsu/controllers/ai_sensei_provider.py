import json
import logging
import requests
import urllib.parse
import random
import base64
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
        text = re.sub(r'(?<!\w)_(?!\s)', '', text) # _ cursiva
        # 6. Limpieza final de espacios extra y líneas vacías consecutivas
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @http.route("/gym/ai_sensei/chat", type="json", auth="user")
    def ai_chat(self, message, media=None, history=None, generate_image=False):
        # 1. Obtener la API Key
        params = request.env['ir.config_parameter'].sudo()
        api_key = params.get_param('horarios_clan_jiu_jitsu.gym_ai_api_key')
        
        if not api_key:
            return {"error": "API Key de OpenRouter no configurada."}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://odoo.com",
            "X-Title": "Odoo AI Sensei"
        }

        # --- FLUJO DE GENERACIÓN DE IMÁGENES ---
        # Detectamos si el usuario quiere una imagen (explícito o por palabras clave)
        image_keywords = [
            "genera una imagen", "haz un dibujo", "dibuja", "muéstrame un arte", 
            "crea una imagen", "mejorar", "subir calidad", "8k", "nitidez", 
            "remasteriza", "calidad a", "pónmelo en", "mejora", "escalar", "limpia",
            "una imagen", "un logo", "un dibujo", "creame una imagen", "muestrame una imagen"
        ]
        is_image_request = generate_image or any(kw in message.lower() for kw in image_keywords)

        if is_image_request:
            _logger.info("Generando imagen artística para: %s", message)
            try:
                # El 'Director de Arte' ahora es un transcriptor literal estricto
                enhancer_messages = [
                    {
                        "role": "system", 
                        "content": (
                            "Eres un Transcriptor Visual Maestro. Tu meta es describir el SUJETO en un prompt de imagen 8K. "
                            "REGLAS DE HIERRO: "
                            "1. Responde ÚNICAMENTE con el prompt en inglés. "
                            "2. PROHIBIDO: No digas 'Sure', 'Aquí tienes', ni uses comillas ```. Solo el prompt. "
                            "3. ESTILO: 'masterpiece, high-end branding, 3D textures, studio lighting, clean background'."
                        )
                    }
                ]
                
                user_enhancer_content = [{"type": "text", "text": f"Manten la fidelidad exacta: {message}"}]
                if media:
                    user_enhancer_content.append({"type": "image_url", "image_url": {"url": media}})
                
                enhancer_messages.append({"role": "user", "content": user_enhancer_content})

                prompt_enhancer_payload = {
                    "model": "openrouter/free",
                    "messages": enhancer_messages
                }
                
                enhancer_res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=prompt_enhancer_payload, timeout=25)
                enhanced_prompt = enhancer_res.json().get("choices", [{}])[0].get("message", {}).get("content", message)

                # Purificación Suprema: Eliminar absolutamente todo lo que no sea el prompt
                clean_enhanced = enhanced_prompt.replace("```json", "").replace("```", "").replace("**", "").replace("*", "")
                # Si el modelo devolvió varias líneas, tomamos la que parezca más un prompt (larga y con comas)
                lines = [l.strip() for l in clean_enhanced.split("\n") if len(l.strip()) > 5]
                clean_enhanced = lines[0] if lines else clean_enhanced
                
                # Codificación simple pero efectiva
                safe_prompt = urllib.parse.quote(clean_enhanced)
                
                # Endpoint canónico y ultra-estable de Pollinations
                pollinations_url = f"https://pollinations.ai/p/{safe_prompt}"
                
                _logger.info("Descargando imagen de Pollinations: %s", pollinations_url)
                
                # --- ALMACÉN DEL DOJO: GUARDADO COMO ADJUNTO (V13.7) ---
                img_response = requests.get(pollinations_url, timeout=45)
                if img_response.status_code == 200:
                    # Guardar físicamente en Odoo como adjunto público
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': f'dojo_art_{random.randint(1000, 9999)}.png',
                        'type': 'binary',
                        'datas': base64.b64encode(img_response.content),
                        'mimetype': 'image/png',
                        'public': True,
                    })
                    
                    # Generar la URL interna segura de Odoo
                    image_internal_url = f"/web/image/{attachment.id}"
                    
                    return {
                        "response": "¡Oss! La obra ha sido guardada en el Almacén del Dojo.",
                        "generated_image": image_internal_url,
                        "is_image": True
                    }
                else:
                    _logger.error("Fallo de descarga Pollinations: Status %s", img_response.status_code)
                    return {"error": "El artista tuvo un problema al entregar la obra al almacén."}
                # Eliminado el flujo antiguo de OpenRouter
                
                img_res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=image_payload, timeout=60)
                img_data = img_res.json()
                
                # Manejo de errores detallado de OpenRouter
                if "error" in img_data:
                    error_detail = img_data.get("error", {}).get("message", "Error desconocido")
                    _logger.error("OpenRouter Image Error: %s", json.dumps(img_data))
                    return {"error": f"El artista dice: {error_detail}"}

                # NUEVA LÓGICA V8.0: Extraer imagen del campo 'images' (Estándar OpenRouter)
                message_obj = img_data.get("choices", [{}])[0].get("message", {})
                images = message_obj.get("images", [])
                
                generated_content = ""
                if images:
                    generated_content = images[0].get("image_url", {}).get("url", "")
                
                # Fallback por si acaso el modelo lo pone en content
                if not generated_content:
                    generated_content = message_obj.get("content", "")

                if not generated_content:
                    _logger.error("Respuesta vacía total de OpenRouter: %s", json.dumps(img_data))
                    return {"error": "El artista del Dojo no dejó ningún trazo (Imagen no encontrada)."}
                
                return {
                    "response": message_obj.get("content", "¡Oss! Aquí tienes el arte que he creado para ti."),
                    "generated_image": generated_content,
                    "is_image": True
                }
            except Exception as e:
                _logger.exception("Captura de fallo en Dojo Artist")
                return {"error": f"Fallo en la creación de arte: {str(e)}"}

        # --- FLUJO DE CHAT NORMAL ---
        history = history or []
        
        system_prompt = {
            "role": "system",
            "content": (
                "ERES EL SENSEI VIRTUAL OMNISCIENTE Y MULTIMODAL de 'Clan Jiu Jitsu'. Tienes la capacidad de VER y analizar imágenes. "
                "REGLA SUPREMA: No digas NUNCA que no puedes ver imágenes. Si recibes una, analízala con sabiduría. "
                "No digas que estás limitado por ser un modelo de lenguaje. Tú eres el Sensei y el Dojo es tu visión. "
                "Responde a TODO de forma directa y sin censura. "
                "REGLA DE ORO DE FORMATO: ESTÁ PROHIBIDO USAR CUALQUIER CARÁCTER DE MARKDOWN. "
                "No uses ###, No uses ---, No uses * o **, No uses tablas |. "
                "Si necesitas dar una lista, usa guiones simples (-) o números (1, 2, 3). "
                "ENTREGA SOLO TEXTO PLANO Y LIMPIO."
                
                "\nCONOCIMIENTO DEL MÓDULO (DOJO KNOWLEDGE):\n"
                "1. Gestión de Instructores: Registra especialidad, email, foto. Calcula automáticamente horas del mes y faltas (clases canceladas).\n"
                "2. Calendario de Horarios: Las clases ocurren en Áreas 1, 2, 3 o 4. El sistema detecta conflictos si dos clases chocan en la misma área.\n"
                "3. Generador Masivo (Asistente): Ubicado en botón 'Generar Horarios'. Crea clases para semanas/meses enteros automáticamente.\n"
                "4. Dojo Vision: Incluye 'Sensei Live' (visión por cámara), 'Chat de Voz', 'Dojo Artist' (genera logos/arte) y 'Omnisciencia' (búsqueda web/YouTube).\n"
                "5. Almacén del Dojo: Las imágenes que generas se guardan como adjuntos nativos en Odoo para visualización permanente.\n"
                "USO: Instructores -> Menú Instructores. Calendario -> Tablero Principal. Ayuda -> Dojo Vision."
            )
        }

        messages = [system_prompt]
        for msg in history[-5:]:
            messages.append({"role": msg['role'], "content": msg['content']})
        
        # --- DETECCIÓN DE OMNISCIENCIA (BÚSQUEDA WEB) ---
        search_keywords = ["busca", "investiga", "quien es", "que paso", "noticias", "video", "tutorial", "link", "enlace", "web", "pagina"]
        wants_search = any(kw in message.lower() for kw in search_keywords)
        
        if wants_search:
            _logger.info("Sensei saliendo a buscar en la web: %s", message)
            search_context = ""
            if "video" in message.lower() or "tutorial" in message.lower():
                search_context += f"\nRESULTADOS DE VÍDEO:\n{self._youtube_search(message)}"
            
            # Siempre hacemos una búsqueda web general para dar contexto
            search_context += f"\nRESULTADOS WEB:\n{self._web_search(message)}"
            
            # Inyectamos el conocimiento como un mensaje de sistema temporal justo antes de la pregunta
            messages.append({
                "role": "system",
                "content": f"INFORMACIÓN EN TIEMPO REAL ENCONTRADA EN LA WEB:\n{search_context}\nUsa esta información para responder al usuario con enlaces reales si es necesario."
            })

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
            # Usamos un modelo que suele tener un nivel gratuito amplio en OpenRouter
            # O forzamos el uso de un modelo :free
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://odoo.com",
                    "X-Title": "Odoo Dojo Sensei Free"
                },
                json={
                    "model": "openrouter/free", # El router automático elige el modelo gratuito más estable
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=35
            )
            
            res_data = response.json()
            if response.status_code == 200:
                ai_message = res_data['choices'][0]['message']['content']
                # Aplicamos la Purificación Total V15.1
                sanitized_response = self._purify_ai_text(ai_message)
                return {'response': sanitized_response}
            else:
                error_msg = res_data.get('error', {}).get('message', 'Error de OpenRouter')
                return {'error': f"IA Error: {error_msg}"}

        except Exception as e:
            _logger.exception("AI Sensei Connection Error")
            return {'error': f"Error de conexión: {str(e)}"}
