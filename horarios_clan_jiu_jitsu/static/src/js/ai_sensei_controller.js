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
        
        this.state = useState({
            messages: [
                { id: 1, role: 'sensei', content: 'Oss. Bienvenido, guerrero. Soy tu Sensei Virtual. ¿Qué estrategia o duda quieres consultar hoy?' }
            ],
            inputContent: '',
            isTyping: false
        });

        // Auto-scroll al final cuando hay nuevos mensajes
        onPatched(() => {
            this.scrollToBottom();
        });
    }

    scrollToBottom() {
        if (this.chatMessagesRef.el) {
            this.chatMessagesRef.el.scrollTop = this.chatMessagesRef.el.scrollHeight;
        }
    }

    async sendMessage() {
        const content = this.state.inputContent.trim();
        if (!content || this.state.isTyping) return;

        // Añadir mensaje del usuario
        const userMsg = { id: Date.now(), role: 'user', content: content };
        this.state.messages.push(userMsg);
        this.state.inputContent = '';
        this.state.isTyping = true;

        try {
            // Llamar al proveedor de IA en el backend
            const result = await rpc("/gym/ai_sensei/chat", {
                message: content,
                history: this.state.messages.map(m => ({ role: m.role === 'sensei' ? 'assistant' : 'user', content: m.content }))
            });

            if (result.error) {
                this.state.messages.push({
                    id: Date.now() + 1,
                    role: 'sensei',
                    content: `⚠️ Error: ${result.error}`
                });
            } else {
                this.state.messages.push({
                    id: Date.now() + 1,
                    role: 'sensei',
                    content: result.response
                });
            }
        } catch (e) {
            this.state.messages.push({
                id: Date.now() + 1,
                role: 'sensei',
                content: "Lo siento, mi conexión espiritual (servidor) ha fallado. Inténtalo de nuevo."
            });
        } finally {
            this.state.isTyping = false;
        }
    }

    onInputKeydown(ev) {
        if (ev.key === "Enter") {
            this.sendMessage();
        }
    }

    sendPrompt(text) {
        this.state.inputContent = text;
        this.sendMessage();
    }

    onBack() {
        this.actionService.doAction({
            type: "ir.actions.client",
            tag: "gym_dashboard_client_action",
        });
    }
}

registry.category("actions").add("ai_sensei_client_action", AISensei);
