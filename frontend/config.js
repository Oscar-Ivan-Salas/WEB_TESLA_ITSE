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
  
 