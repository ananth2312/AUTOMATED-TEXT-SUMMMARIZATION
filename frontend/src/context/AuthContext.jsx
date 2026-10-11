// src/context/AuthContext.jsx
// ───────────────────────────
// Provides authentication state throughout the app.
// Stores the JWT in localStorage (access token only – no refresh token in MVP).
// Exports useAuth() hook for components.

import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)  // true while validating stored token

  // On mount: validate any stored token by fetching /api/auth/me
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) { setLoading(false); return }

    api.get('/auth/me')
      .then(res => setUser(res.data))
      .catch(() => { localStorage.removeItem('access_token') })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email, password) => {
    const res = await api.post('/auth/login', { email, password })
    const { access_token } = res.data
    localStorage.setItem('access_token', access_token)
    const me = await api.get('/auth/me')
    setUser(me.data)
    return me.data
  }, [])

  const register = useCallback(async (name, email, password) => {
    await api.post('/auth/register', { name, email, password })
    return login(email, password)
  }, [login])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    setUser(null)
  }, [])

  const updateUser = useCallback((partial) => {
    setUser(prev => ({ ...prev, ...partial }))
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
