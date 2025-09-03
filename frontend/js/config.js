// Configuración de la API
window.API_CONFIG = {
  // En desarrollo, usa localhost:8000
  // En producción, se deja vacío para rutas relativas
  BASE_URL: (() => {
    return window.location.hostname === 'localhost' || 
           window.location.hostname === '127.0.0.1'
      ? 'http://127.0.0.1:8000'
      : '';
  })(),
  
  // Endpoints
  ENDPOINTS: {
    HEALTH: '/healthz',
    METRICS: '/api/metrics',
    CHAT: '/api/chat',
    LEADS: '/api/leads'
  },
  
  // Configuración del chat
  CHAT: {
    DEFAULT_MESSAGE: 'Hola, ¿en qué puedo ayudarte hoy?',
    ERROR_MESSAGE: 'Lo siento, ha ocurrido un error. Por favor, inténtalo de nuevo más tarde.'
  }
};

// Hacer la configuración disponible globalmente
console.log('API Config:', window.API_CONFIG);
