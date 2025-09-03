/**
 * Módulo para manejar las llamadas a la API
 */

class ApiService {
  constructor() {
    this.baseUrl = window.API_CONFIG.BASE_URL;
    this.endpoints = window.API_CONFIG.ENDPOINTS;
  }

  /**
   * Realiza una petición a la API
   * @param {string} endpoint - Endpoint de la API
   * @param {Object} options - Opciones de la petición
   * @returns {Promise<Object>} - Respuesta de la API
   */
  async fetchApi(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, defaultOptions);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || 'Error en la petición');
      }

      // Si la respuesta es 204 No Content, retornamos null
      if (response.status === 204) {
        return null;
      }

      return await response.json();
    } catch (error) {
      console.error('Error en la petición:', error);
      throw error;
    }
  }

  // Métodos específicos de la API

  /**
   * Verifica el estado del servidor
   * @returns {Promise<Object>} - Estado del servidor
   */
  async checkHealth() {
    return this.fetchApi(this.endpoints.HEALTH);
  }

  /**
   * Obtiene las métricas del dashboard
   * @returns {Promise<Object>} - Métricas del dashboard
   */
  async getMetrics() {
    return this.fetchApi(this.endpoints.METRICS);
  }

  /**
   * Envía un mensaje al chat
   * @param {string} message - Mensaje del usuario
   * @param {boolean} useAi - Usar IA para la respuesta
   * @returns {Promise<Object>} - Respuesta del chat
   */
  async sendChatMessage(message, useAi = true) {
    return this.fetchApi(this.endpoints.CHAT, {
      method: 'POST',
      body: JSON.stringify({ message, use_ai: useAi }),
    });
  }

  /**
   * Envía un lead
   * @param {Object} lead - Datos del lead
   * @returns {Promise<Object>} - Respuesta del servidor
   */
  async sendLead(lead) {
    return this.fetchApi(this.endpoints.LEADS, {
      method: 'POST',
      body: JSON.stringify(lead),
    });
  }
}

// Exportar una instancia del servicio
const apiService = new ApiService();

export default apiService;
