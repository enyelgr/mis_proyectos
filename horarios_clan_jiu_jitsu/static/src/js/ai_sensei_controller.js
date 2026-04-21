/** @odoo-module **/
import { Component, useState, useRef, onPatched, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class AISensei extends Component {
    static template = "horarios_clan_jiu_jitsu.AISensei";

    setup() {
        this.actionService = useService("action");
        this.chatMessagesRef = useRef("chatMessages");
        this.webcamVideoRef = useRef("webcamVideo");
        this.snapshotCanvasRef = useRef("snapshotCanvas");
        
        this.state = useState({
            messages: [
                { id: 1, role: 'sensei', content: 'Oss. Bienvenido, guerrero. Soy tu Sensei Virtual. ¿Qué estrategia o duda quieres consultar hoy?' }
            ],
            inputContent: '',
            isTyping: false,
            isLive: false,
            isVoiceOnly: false,
            isListening: false,
            autoSpeak: false,
            pendingMedia: null
        });

        // Configuración de Reconocimiento de Voz
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            this.recognition = new SpeechRecognition();
            this.recognition.lang = 'es-ES';
            this.recognition.continuous = false;
            this.recognition.interimResults = false;

            this.recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                this.state.inputContent = text;
                this.state.isListening = false;
                this.sendMessage();
            };

            this.recognition.onerror = () => {
                this.state.isListening = false;
            };
        }

        onPatched(() => this.scrollToBottom());
    }

    scrollToBottom() {
        if (this.chatMessagesRef.el) {
            this.chatMessagesRef.el.scrollTop = this.chatMessagesRef.el.scrollHeight;
        }
    }

    // --- FILTROS Y TOGGLES ---
    toggleAutoSpeak() {
        this.state.autoSpeak = !this.state.autoSpeak;
        if (this.state.autoSpeak) {
            this.speak("Respuesta por voz activada.");
        } else {
            window.speechSynthesis.cancel();
        }
    }

    // --- MANEJO DE VOZ ---
    toggleVoiceInput() {
        if (!this.recognition) return alert("Tu navegador no soporta reconocimiento de voz.");
        if (this.state.isListening) {
            this.recognition.stop();
        } else {
            this._startListening();
        }
    }

    _startListening() {
        if (this.recognition && !this.state.isListening) {
            try {
                this.state.isListening = true;
                this.recognition.start();
            } catch (e) {
                console.log("Recognition already started or error:", e);
            }
        }
    }

    speak(text) {
        if (!window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'es-ES';
        utterance.rate = 1.0;

        // Al terminar de hablar, si estamos en modo Live o VoiceOnly, volvemos a escuchar automáticamente
        utterance.onend = () => {
            if (this.state.isLive || this.state.isVoiceOnly) {
                this._startListening();
            }
        };

        window.speechSynthesis.speak(utterance);
    }

    // --- MANEJO DE MODOS INTERACTIVOS ---
    async toggleLiveMode() {
        if (this.state.isLive) {
            this.stopLiveMode();
        } else {
            if (this.state.isVoiceOnly) this.stopVoiceOnlyMode();
            await this.startLiveMode();
        }
    }

    async toggleVoiceOnlyMode() {
        if (this.state.isVoiceOnly) {
            this.stopVoiceOnlyMode();
        } else {
            if (this.state.isLive) this.stopLiveMode();
            await this.startVoiceOnlyMode();
        }
    }

    async startLiveMode() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: true });
            this.state.isLive = true;
            this.stream = stream;
            setTimeout(() => {
                if (this.webcamVideoRef.el) {
                    this.webcamVideoRef.el.srcObject = stream;
                    this.webcamVideoRef.el.muted = true;
                }
            }, 100);
            this.speak("Modo Live activado. Estoy viéndote.");
            setTimeout(() => this._startListening(), 2000);
        } catch (err) { alert("Error cámara: " + err.message); }
    }

    async startVoiceOnlyMode() {
        try {
            // Solo pedimos audio
            const stream = await navigator.mediaDevices.getUserMedia({ video: false, audio: true });
            this.state.isVoiceOnly = true;
            this.stream = stream;
            this.speak("Chat de voz activado. Te escucho, guerrero.");
            setTimeout(() => this._startListening(), 2000);
        } catch (err) { alert("Error micro: " + err.message); }
    }

    stopLiveMode() {
        if (this.stream) this.stream.getTracks().forEach(t => t.stop());
        if (this.recognition) this.recognition.stop();
        this.state.isLive = false;
        this.state.isListening = false;
        window.speechSynthesis.cancel();
    }

    stopVoiceOnlyMode() {
        if (this.stream) this.stream.getTracks().forEach(t => t.stop());
        if (this.recognition) this.recognition.stop();
        this.state.isVoiceOnly = false;
        this.state.isListening = false;
        window.speechSynthesis.cancel();
    }

    takeSnapshot() {
        if (!this.webcamVideoRef.el || !this.snapshotCanvasRef.el) return null;
        const video = this.webcamVideoRef.el;
        const canvas = this.snapshotCanvasRef.el;
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        return canvas.toDataURL('image/jpeg', 0.7);
    }

    // --- MANEJO DE ARCHIVOS ---
    onFileChange(ev) {
        const file = ev.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            this.state.pendingMedia = e.target.result;
            this.sendMessage();
        };
        reader.readAsDataURL(file);
    }

    // --- ENVÍO DE MENSAJES ---
    async sendMessage() {
        const content = this.state.inputContent.trim();
        const media = this.state.pendingMedia || (this.state.isLive ? this.takeSnapshot() : null);
        
        if (!content && !media) return;
        if (this.state.isTyping) return;

        // Añadir mensaje visual del usuario
        const msgId = Date.now();
        if (content) {
            this.state.messages.push({ id: msgId, role: 'user', content: content });
        }
        if (media && !this.state.isLive) {
            this.state.messages.push({ id: msgId + 1, role: 'user', content: media, isImage: true });
        }

        this.state.inputContent = '';
        this.state.pendingMedia = null;
        this.state.isTyping = true;

        try {
            // Llamar al proveedor
            const result = await rpc("/gym/ai_sensei/chat", {
                message: content || "Analiza esta imagen del dojo.",
                media: media,
                history: this.state.messages.map(m => ({ 
                    role: m.role === 'sensei' ? 'assistant' : 'user', 
                    content: m.isImage ? "Envié una imagen." : m.content 
                }))
            });

            if (result.error) {
                this.addSenseiMessage(`⚠️ ${result.error}`);
            } else {
                this.addSenseiMessage(result.response);
                // Si el modo voz (autoSpeak) está activo o estamos en modo VoiceOnly, el Sensei habla
                if (this.state.autoSpeak || this.state.isVoiceOnly || this.state.isLive) {
                    this.speak(result.response);
                }
            }
        } catch (e) {
            this.addSenseiMessage("Mi conexión espiritual falló. Inténtalo de nuevo.");
        } finally {
            this.state.isTyping = false;
        }
    }

    addSenseiMessage(text) {
        this.state.messages.push({ id: Date.now(), role: 'sensei', content: text });
    }

    onInputKeydown(ev) {
        if (ev.key === "Enter") this.sendMessage();
    }

    sendPrompt(text) {
        this.state.inputContent = text;
        this.sendMessage();
    }

    onBack() {
        this.stopLiveMode();
        this.actionService.doAction({
            type: "ir.actions.client",
            tag: "gym_dashboard_client_action",
        });
    }
}

registry.category("actions").add("ai_sensei_client_action", AISensei);
