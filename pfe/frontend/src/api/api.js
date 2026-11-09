import axios from 'axios';

// In dev, use relative URL so Vite proxy sends requests to backend (no CORS, Authorization always sent).
// In production, use full backend URL or same relative /api/v1 if served with same server.
// In dev, use the Vite proxy so the browser treats it as same-origin (avoids CORS + "Network Error").
const baseURL = import.meta.env?.DEV
  ? '/api/v1'
  : (import.meta.env?.VITE_API_URL || 'http://127.0.0.1:8000/api/v1');

// Prevent indefinite hangs (frozen loaders / stuck Dialog saves when backend never responds).
const DEFAULT_TIMEOUT_MS = 45000;

const api = axios.create({
  baseURL,
  timeout: DEFAULT_TIMEOUT_MS,
});

function getToken() {
  let rawAccess = null;
  let rawLegacy = null;
  try {
    rawAccess = localStorage.getItem('access_token');
    rawLegacy = localStorage.getItem('token');
  } catch {
    return null;
  }
  const t = rawAccess || rawLegacy;
  return t && typeof t === 'string' && t !== 'undefined' && t !== 'null' ? t.trim() : null;
}

function setAuthHeader(token) {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
}

// Sync default header on load (e.g. after refresh)
const initialToken = getToken();
if (initialToken) setAuthHeader(initialToken);

// Attach Authorization to every request so protected endpoints succeed
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    const value = `Bearer ${token}`;
    api.defaults.headers.common['Authorization'] = value;
    // Axios 1.x: config.headers may be AxiosHeaders; set in a way that is always sent
    if (config.headers) {
      if (typeof config.headers.set === 'function') {
        config.headers.set('Authorization', value);
      } else {
        config.headers['Authorization'] = value;
        config.headers['authorization'] = value;
      }
    } else {
      config.headers = { Authorization: value };
    }
  }
  if (import.meta.env?.DEV && !config.url?.includes('/auth/')) {
    console.debug('[api]', config.method?.toUpperCase(), config.url, token ? '(with token)' : '(no token)');
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      try {
        localStorage.removeItem('access_token');
        localStorage.removeItem('token');
      } catch {
        // Ignore storage failures; auth header is still cleared below.
      }
      setAuthHeader(null);
    }
    return Promise.reject(error);
  }
);

export default api;
export { setAuthHeader, getToken };
