// src/services/api.js
// ────────────────────
// Axios instance pre-configured with:
// - Base URL from Vite env (default: /api via the Vite proxy)
// - Automatic Bearer token injection from localStorage
// - 401 → clear token and redirect to /login

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 60000,   // 60s – analysis can take a few seconds
})

// Attach token to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle expired/invalid tokens globally
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      // Only redirect if not already on the login page
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  },
)

export default api

// ── Typed service helpers ─────────────────────────────────────────────────────

export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login:    (data) => api.post('/auth/login',    data),
  me:       ()     => api.get('/auth/me'),
  updateProfile:   (data) => api.patch('/auth/profile', data),
  changePassword:  (data) => api.post('/auth/change-password', data),
}

export const documentsApi = {
  upload: (formData) => api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  importExternal: (data) => api.post('/documents/import-external', data),
  previewExternal: (data) => api.post('/documents/preview-external', data),
  getPdfBlob: (id) => api.get(`/documents/${id}/pdf`, { responseType: 'blob' }),
  list:   (params) => api.get('/documents', { params }),
  get:    (id)     => api.get(`/documents/${id}`),
  delete: (id)     => api.delete(`/documents/${id}`),
}


export const analysesApi = {
  analyzeText:     (data)          => api.post('/analyses/text', data),
  analyzeDocument: (docId, data)   => api.post(`/documents/${docId}/analyze`, data),
  list:            (params)        => api.get('/analyses', { params }),
  get:             (id)            => api.get(`/analyses/${id}`),
  exportTxt:       (id)            => api.get(`/analyses/${id}/export?format=txt`, { responseType: 'blob' }),
  exportPdf:       (id)            => api.get(`/analyses/${id}/export?format=pdf`, { responseType: 'blob' }),
  dashboard:       ()              => api.get('/dashboard'),
}
