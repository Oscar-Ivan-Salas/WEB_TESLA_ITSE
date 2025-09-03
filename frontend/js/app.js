/**
 * Punto de entrada principal de la aplicación
 */

import apiService from './api.js';

class App {
  constructor() {
    this.api = apiService;
    this.initializeApp();
  }

  /**
   * Inicializa la aplicación
   */
  async initializeApp() {
    try {
      // Verificar conexión con el backend
      await this.checkBackendConnection();
      
      // Cargar métricas iniciales
      await this.loadMetrics();
      
      // Inicializar manejadores de eventos
      this.initializeEventListeners();
      
      console.log('Aplicación inicializada correctamente');
    } catch (error) {
      console.error('Error al inicializar la aplicación:', error);
      this.showNotification('Error al conectar con el servidor', 'error');
    }
  }

  /**
   * Verifica la conexión con el backend
   */
  async checkBackendConnection() {
    try {
      await this.api.checkHealth();
      this.updateConnectionStatus(true);
    } catch (error) {
      console.error('No se pudo conectar al backend:', error);
      this.updateConnectionStatus(false);
      throw error;
    }
  }

  /**
   * Actualiza el estado de conexión en la interfaz
   * @param {boolean} isConnected - Indica si hay conexión
   */
  updateConnectionStatus(isConnected) {
    const statusElement = document.getElementById('connection-status');
    if (!statusElement) return;

    if (isConnected) {
      statusElement.textContent = 'Conectado al servidor';
      statusElement.className = 'status-connected';
    } else {
      statusElement.textContent = 'Sin conexión al servidor';
      statusElement.className = 'status-disconnected';
    }
  }

  /**
   * Carga las métricas del dashboard
   */
  async loadMetrics() {
    try {
      const metrics = await this.api.getMetrics();
      this.updateMetricsUI(metrics);
    } catch (error) {
      console.error('Error al cargar métricas:', error);
      // Usar datos de ejemplo si falla la carga
      this.updateMetricsUI({
        itse: 80,
        pozo: 65,
        mant: 90,
        inc: 50
      });
    }
  }

  /**
   * Actualiza la interfaz con las métricas
   * @param {Object} metrics - Métricas a mostrar
   */
  updateMetricsUI(metrics) {
    // Actualizar gráficos de barras
    const bars = document.querySelectorAll('.chart .bar');
    const keys = ['itse', 'pozo', 'mant', 'inc'];
    
    bars.forEach((bar, index) => {
      const key = keys[index];
      const value = metrics[key] || 50; // Valor por defecto si no existe
      bar.style.height = `${Math.max(5, Math.min(100, value))}%`;
      
      // Actualizar tooltip
      const tip = bar.querySelector('.tip');
      if (tip) {
        tip.textContent = `${value}%`;
      }
    });
  }

  /**
   * Inicializa los manejadores de eventos
   */
  initializeEventListeners() {
    // Manejador para el formulario de contacto
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
      contactForm.addEventListener('submit', (e) => this.handleContactSubmit(e));
    }

    // Manejador para el chat
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
      chatForm.addEventListener('submit', (e) => this.handleChatSubmit(e));
    }
  }

  /**
   * Maneja el envío del formulario de contacto
   * @param {Event} e - Evento de envío del formulario
   */
  async handleContactSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.textContent;
    
    try {
      // Deshabilitar botón y mostrar estado de carga
      submitButton.disabled = true;
      submitButton.textContent = 'Enviando...';
      
      // Validar datos del formulario
      const name = formData.get('name')?.trim();
      const email = formData.get('email')?.trim();
      const phone = formData.get('phone')?.trim();
      const message = formData.get('message')?.trim();
      
      if (!name || !email || !phone) {
        throw new Error('Por favor complete todos los campos obligatorios');
      }
      
      // Validar formato de email
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        throw new Error('Por favor ingrese un correo electrónico válido');
      }
      
      // Enviar datos al servidor
      await this.api.sendLead({
        name,
        email,
        phone,
        message: message || 'Sin mensaje adicional',
        source: 'formulario-web'
      });
      
      // Mostrar mensaje de éxito
      this.showNotification('¡Mensaje enviado con éxito!', 'success');
      form.reset();
      
    } catch (error) {
      console.error('Error al enviar el formulario:', error);
      this.showNotification(
        error.message || 'Error al enviar el mensaje. Por favor, intente nuevamente.',
        'error'
      );
    } finally {
      // Restaurar botón
      submitButton.disabled = false;
      submitButton.textContent = originalButtonText;
    }
  }

  /**
   * Maneja el envío de mensajes en el chat
   * @param {Event} e - Evento de envío del formulario de chat
   */
  async handleChatSubmit(e) {
    e.preventDefault();
    
    const input = e.target.querySelector('input[type="text"]');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Mostrar mensaje del usuario
    this.appendMessage(message, 'user');
    input.value = '';
    
    try {
      // Mostrar indicador de escritura
      this.showTypingIndicator();
      
      // Enviar mensaje al servidor
      const response = await this.api.sendChatMessage(message);
      
      // Ocultar indicador y mostrar respuesta
      this.hideTypingIndicator();
      this.appendMessage(response.reply, 'bot');
      
    } catch (error) {
      console.error('Error en el chat:', error);
      this.hideTypingIndicator();
      this.appendMessage(
        'Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, inténtalo de nuevo más tarde.',
        'bot'
      );
    }
  }

  /**
   * Agrega un mensaje al chat
   * @param {string} text - Texto del mensaje
   * @param {string} sender - Remitente ('user' o 'bot')
   */
  appendMessage(text, sender = 'bot') {
    const chatContainer = document.querySelector('.chat-messages');
    if (!chatContainer) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `chat-message ${sender}`;
    messageElement.innerHTML = `
      <div class="message-content">
        <div class="message-text">${this.escapeHtml(text)}</div>
        <div class="message-time">${this.getCurrentTime()}</div>
      </div>
    `;
    
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  /**
   * Muestra el indicador de escritura
   */
  showTypingIndicator() {
    const chatContainer = document.querySelector('.chat-messages');
    if (!chatContainer) return;
    
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.id = 'typing-indicator';
    indicator.innerHTML = `
      <div class="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
    `;
    
    chatContainer.appendChild(indicator);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  /**
   * Oculta el indicador de escritura
   */
  hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
      indicator.remove();
    }
  }

  /**
   * Muestra una notificación al usuario
   * @param {string} message - Mensaje a mostrar
   * @param {string} type - Tipo de notificación ('success', 'error', 'warning', 'info')
   */
  showNotification(message, type = 'info') {
    // Implementar lógica para mostrar notificaciones
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Aquí podrías integrar con alguna librería de notificaciones
    // o implementar tu propio sistema de notificaciones
  }

  // Utilidades
  
  /**
   * Escapa caracteres HTML para prevenir XSS
   * @param {string} text - Texto a escapar
   * @returns {string} - Texto escapado
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Obtiene la hora actual formateada
   * @returns {string} - Hora en formato HH:MM
   */
  getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
  try {
    const app = new App();
    window.app = app; // Hacer accesible desde la consola para depuración
  } catch (error) {
    console.error('Error al inicializar la aplicación:', error);
  }
});
